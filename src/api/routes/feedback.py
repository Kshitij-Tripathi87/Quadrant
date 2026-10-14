from fastapi import APIRouter, status, HTTPException
from src.api.schemas import FeedbackRequest, FeedbackResponse
from src.storage.repository import storage_repo

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user feedback on an answer",
    description="Records thumbs up or thumbs down rating and an optional user comment for evaluation."
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    if request.rating not in ["up", "down"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be either 'up' or 'down'."
        )

    try:
        feedback_id = storage_repo.save_feedback(
            query_id=request.query_id,
            rating=request.rating,
            comment=request.comment,
        )

        return FeedbackResponse(
            feedback_id=feedback_id,
            status="recorded",
            message="Feedback successfully recorded. Thank you for helping evaluate our RAG assistant!"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )
