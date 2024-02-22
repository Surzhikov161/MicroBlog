from typing import List, Optional

from pydantic import BaseModel


class ReturnModel(BaseModel):
    result: bool


class ReturnModelWithMsg(ReturnModel):
    msg: str


class TweetModel(BaseModel):
    tweet_data: str
    tweet_media_ids: Optional[List[int]]


class TweetResult(BaseModel):
    result: bool
    tweet_id: int


class UserBase(BaseModel):
    id: int
    name: str


class UserLike(BaseModel):
    user_id: int
    name: str


class UserFollow(UserBase):
    followers: Optional[List["UserBase"]]
    following: Optional[List["UserBase"]]


class UserModel(BaseModel):
    result: bool
    user: UserFollow


class TweetOut(BaseModel):
    id: int
    content: str
    attachments: Optional[List[str]]
    author: "UserBase"
    likes: Optional[List["UserLike"]]


class FeedModel(ReturnModel):
    tweets: Optional[List["TweetOut"]]


class ErrorModel(ReturnModel):
    error_type: str
    error_message: str


class MediaModel(ReturnModel):
    media_id: int
