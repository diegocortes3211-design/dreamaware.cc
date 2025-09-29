from fastapi import APIRouter, HTTPException
from .models import PatchReq, PatchResp
from .main import apply_patch, ValidationError, PatchError

router = APIRouter(prefix="/v1/action", tags=["action"])

@router.post("/patch", response_model=PatchResp)
async def apply_patch_endpoint(req: PatchReq):
    try:
        # The request object 'req' is already a Pydantic model,
        # so we can convert it to a dict to pass to the apply_patch function.
        result = await apply_patch(
            planId=req.planId,
            stepId=req.stepId,
            repo=req.repo,
            branch=req.branch,
            diff=req.diff,
            commitMessage=req.commitMessage,
            author=req.author
        )
        return result
    except ValidationError as e:
        # Pydantic's own validation will typically catch this before we do,
        # but this is good practice for custom validation logic.
        raise HTTPException(status_code=400, detail=str(e))
    except PatchError as e:
        # This exception is for errors during the patch process itself.
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        # Catch any other unexpected errors.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")