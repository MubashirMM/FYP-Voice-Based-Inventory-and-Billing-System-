from pydantic import BaseModel ,ConfigDict
class Customers(BaseModel):
    customer_name:str

class CustomerCreate(Customers):
    pass 

class CustomerRead(Customers):
    customer_id:int
    model_config=ConfigDict(from_attributes=True)
