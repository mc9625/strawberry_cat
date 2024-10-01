from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field

class StrawberryCatSettings(BaseModel):
    trigger: str = Field(
        title="The prefix that will trigger the reasoning.",
        default="Q*"
    )
    # Reasoning Display Option
    show_reasoning: bool = Field(
        default=True,
        description="If On, the answer will include the full reasoning."
    )
@plugin
def settings_model():
    return StrawberryCatSettings
