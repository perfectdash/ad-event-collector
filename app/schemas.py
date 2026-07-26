from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import re
from datetime import datetime

class AdEvent(BaseModel):
    
    event_id: str = Field(..., description="Unique identifier (UUID v4) for the event")
    timestamp: str = Field(..., description="ISO 8601 format timestamp of the event")
    campaign_id: str = Field(..., description="Target Campaign ID")
    advertiser_id: str = Field(..., description="Target Advertiser ID")
    event_type: Literal["click", "impression", "conversion"] = Field(..., description="Type of the ad event")
    cost: float = Field(default=0.0, ge=0.0, description="Cost associated with the event (e.g., CPC, CPM, CPA)")
    user_agent: Optional[str] = Field(default=None, description="Client user agent string")
    ip_address: Optional[str] = Field(default=None, description="IP address of the client")

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        # I did this to verify UUID format
        uuid_regex = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
        if not uuid_regex.match(v):
            raise ValueError("event_id must be a valid UUID v4")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        # I did this to verify that the timestamp is a valid datetime format
        try:
            # I did this to support ISO 8601 strings ending in Z or offsets
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("timestamp must be in a valid ISO 8601 format")
        return v


    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        if not v.startswith("camp-"):
            raise ValueError("campaign_id must start with prefix 'camp-'")
        return v

    @field_validator("advertiser_id")
    @classmethod
    def validate_advertiser_id(cls, v: str) -> str:
        if not v.startswith("adv-"):
            raise ValueError("advertiser_id must start with prefix 'adv-'")
        return v
