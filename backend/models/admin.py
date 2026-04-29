from pydantic import BaseModel, Field

class WorkerCreateIn(BaseModel):
    first_name: str
    last_name: str

class WorkerUpdateIn(BaseModel):    
    first_name: str
    last_name: str      
    username: str   
    auth_provider: str
    ldap_dn: str | None = None
    is_admin: bool = False
    is_active: bool = True

class UpdateWorkerAdminIn(BaseModel):
    is_admin: bool


class AdminResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=8)

class ProductCreateIn(BaseModel):
    category_id: int
    brand_id: int
    product_name: str
    nc_nummer: str | None = None
    active: bool = True

class ProductUpdateIn(BaseModel):
    category_id: int
    brand_id: int
    product_name: str
    nc_nummer: str | None = None
    active: bool = True


class CategoryCreateIn(BaseModel):
    name: str


class CategoryUpdateIn(BaseModel):
    name: str
    active: bool = True


class BrandCreateIn(BaseModel):
    name: str


class BrandUpdateIn(BaseModel):
    name: str
    active: bool = True


class SiteCreateIn(BaseModel):
    name: str


class SiteUpdateIn(BaseModel):
    name: str
    active: bool = True


class LocationCreateIn(BaseModel):
    site_id: int
    shelf: int
    row: int
    active: bool = True


class LocationUpdateIn(BaseModel):
    site_id: int
    shelf: int
    row: int
    active: bool = True


class ProductSiteLocationUpsertIn(BaseModel):
    site_id: int
    location_id: int