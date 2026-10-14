# LangGraph Core Concepts and StateGraph Workflows

LangGraph is a library designed for building stateful, multi-actor applications with LLMs. It extends LangChain to support cyclic computation graphs, enabling agent loops, self-correction, and human-in-the-loop patterns.

## 1. Why LangGraph?
Standard chains in LangChain are Directed Acyclic Graphs (DAGs) which execute sequentially from input to output. However, advanced agentic patterns like **Corrective RAG (CRAG)** and **Self-RAG** require:
- **Loops & Cycles**: Iteratively rewriting queries or regenerating answers if an evaluation fails.
- **State Persistence**: A single central state object passed and updated across nodes.
- **Conditional Branching**: Dynamic routing based on intermediate LLM evaluation scores.

## 2. Core Building Blocks

### StateGraph & State Schema
The foundation of any LangGraph workflow is a centralized state defined using `typing.TypedDict` or Pydantic:

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    question: str
    documents: List[str]
    generation: str
    retry_count: int
```

Each node in the graph receives the current state and returns a dictionary with updated key-value pairs.

### Nodes
Nodes are standard Python functions or runnables that take `state` and return an update:

```python
def retrieve_node(state: AgentState):
    question = state["question"]
    docs = vector_store.similarity_search(question, k=4)
    return {"documents": docs}

def generate_node(state: AgentState):
    context = "\n".join(state["documents"])
    response = llm.invoke(f"Context: {context}\nQuestion: {state['question']}")
    return {"generation": response.content}
```

### Normal Edges & Conditional Edges
- **Normal Edges (`add_edge`)**: Connect node A directly to node B.
- **Conditional Edges (`add_conditional_edges`)**: Route to different target nodes based on a router function output.

```python
def check_documents_relevance(state: AgentState) -> str:
    if len(state["documents"]) > 0:
        return "generate"
    elif state["retry_count"] < 2:
        return "rewrite"
    else:
        return "fallback"

workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.add_node("rewrite", rewrite_query_node)

workflow.add_edge(START, "retrieve")
workflow.add_conditional_edges(
    "retrieve",
    check_documents_relevance,
    {
        "generate": "generate",
        "rewrite": "rewrite",
        "fallback": "fallback"
    }
)
workflow.add_edge("generate", END)
```

## 3. Self-Corrective RAG (CRAG) Pattern
In Corrective RAG:
1. Retrieval is performed.
2. A Document Evaluator grades retrieved chunks as relevant or irrelevant.
3. If irrelevant, a query rewriting node modifies the query and increments a retry counter.
4. The graph re-retrieves candidate chunks.
5. If retries exceed maximum threshold (e.g. `retry_count >= 2`), a fallback path (e.g. web search) is triggered to avoid infinite loops.

## 4. Compilation & Execution
Once all nodes and edges are added, the graph is compiled:
```python
app = workflow.compile()
final_state = app.invoke({"question": "What is StateGraph?", "retry_count": 0})
```
