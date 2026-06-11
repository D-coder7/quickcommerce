from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None


class CategoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    description: str | None


class ProductCreate(BaseModel):
    category_id: int
    name: str
    slug: str
    description: str | None = None
    price: float
    image_url: str | None = None


class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    category_id: int
    name: str
    slug: str
    description: str | None
    price: float
    image_url: str | None
    is_active: bool


class ProductDetailResponse(ProductResponse):
    category: CategoryResponse
    available_quantity: int = 0
