from bson.errors import InvalidId  # Import this for error handling
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder
from datetime import datetime


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


app = FastAPI()
uri = "mongodb+srv://priyankraychura:f6yWILYS7Q2dZRWQ@jobsearch-dev.aqsw6.mongodb.net/?retryWrites=true&w=majority&appName=JobSearch-Dev"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["job_app"]  # Correct database name

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

class Job(BaseModel):
    id: Optional[str] = Field(None, alias="_id")  # Map `_id` to `id`
    title: str
    org_name: str
    employer_name: str
    desc: str
    req_skills: List[str]

class Employer(BaseModel):
    e_id: str
    name: str
    email: str
    profile_picture: str
    designation: str
    orgname: str
    password: str

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")  # Field alias for `_id`
    # _id: str  # Add `_id` field for MongoDB ObjectId
    name: str
    email: str
    emailVarified: bool = False
    profile_picture: str = ""
    social_link: str = ""
    password: str
    phone: str = ""
    education: List[dict] = []
    skills: str = ""
    experience: List[dict] = []
    languages: str = ""

class Application(BaseModel):
    id: Optional[str] = Field(None, alias="_id")  # Alias `_id` to `id` for consistency
    user_id: str
    job_id: str
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    status: str = "Pending"
    applied_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


@app.get("/jobs", response_model=List[Job])
async def read_jobs():
    jobs = db.job.find()  # Fetch all jobs, including `_id`
    # Convert `_id` to string and include it in the response
    return [
        {**job, "_id": str(job["_id"])} for job in jobs
    ]

@app.post("/job", response_model=Job)  # Changed endpoint and model
async def create_job(job: Job):
    db.job.insert_one(job.dict())  # Correct collection name
    return job


@app.get("/job/{job_id}", response_model=Job)
async def get_job(job_id: str):
    """
    Fetch a single job by its ID.
    """
    try:
        # Attempt to convert the string `job_id` to an ObjectId
        job = db.job.find_one({"_id": ObjectId(job_id)})
    except InvalidId:
        # Handle cases where the provided ID is not a valid ObjectId
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if job:
        # Convert `_id` to a string and include it in the response
        job["_id"] = str(job["_id"])
        return job
    
    # Raise an error if the job is not found
    raise HTTPException(status_code=404, detail="Job not found")



# employer
@app.get("/employers", response_model=List[Employer])
async def read_employers():
    employers = list(db.employer.find({}, {'_id': False}))
    return employers
# Create employer
@app.post("/employer", response_model=Employer)
async def create_employer(employer: Employer):
    employer_dict = jsonable_encoder(employer)
    if db.employer.find_one({"e_id": employer.e_id}):
        raise HTTPException(status_code=400, detail="Employer with this e_id already exists")
    db.employer.insert_one(employer_dict)
    return employer_dict

# Get employer by ID
@app.get("/employer/{employer_id}", response_model=Employer)
async def get_employer(employer_id: str):
    employer = db.employer.find_one({"e_id": employer_id}, {'_id': False})
    if employer:
        return employer
    raise HTTPException(status_code=404, detail="Employer not found")



# user
@app.get("/users", response_model=List[User])
async def read_users():
    users = db.users.find()  # Include `_id`
    return [
        {**user, "_id": str(user["_id"])}  # Convert `_id` to string
        for user in users
    ]

# Create user
@app.post("/user", response_model=User)
async def create_user(user: User):
    user_dict = jsonable_encoder(user, exclude={"id"})  # Exclude 'id' from request payload
    
    # Check if a user with the given email already exists
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Insert the new user
    result = db.users.insert_one(user_dict)
    
    # Add the auto-generated _id to the response
    user_dict["_id"] = str(result.inserted_id)  # Include generated `_id`
    return user_dict



# Get user by ID
@app.get("/user/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = db.users.find_one({"_id": ObjectId(user_id)})  # Query by ObjectId
    if user:
        user["_id"] = str(user["_id"])  # Convert `_id` to string
        return user
    raise HTTPException(status_code=404, detail="User not found")

from fastapi import Body

@app.put("/user/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    try:
        # Check if the user exists
        existing_user = db.users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the user
        user_dict = jsonable_encoder(user, exclude={"id"})
        db.users.replace_one({"_id": ObjectId(user_id)}, user_dict)

        # Add the updated `_id` to the response
        user_dict["_id"] = str(user_id)
        return user_dict
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

@app.patch("/user/{user_id}", response_model=User)
async def partial_update_user(user_id: str, updates: dict = Body(...)):
    try:
        # Check if the user exists
        existing_user = db.users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Apply updates
        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})

        # Fetch the updated user
        updated_user = db.users.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])
        return updated_user
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID format")



# Applications Collection
@app.post("/application", response_model=Application)
async def create_application(application: Application):
    # Check if user and job exist
    if not db.users.find_one({"_id": ObjectId(application.user_id)}):
        raise HTTPException(status_code=404, detail="User not found")
    if not db.job.find_one({"_id": ObjectId(application.job_id)}):
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Insert application
    application_dict = jsonable_encoder(application, exclude={"id"})
    result = db.applications.insert_one(application_dict)
    application_dict["_id"] = str(result.inserted_id)
    return application_dict

# @app.get("/applications", response_model=List[Application])
# async def list_applications():
#     # Fetch all applications
#     applications = db.applications.find()
#     # Convert _id (ObjectId) to string for JSON serialization
#     return [
#         {**app, "_id": str(app["_id"])} for app in applications
#     ]


@app.get("/applications/{application_id}", response_model=Application)
async def get_application(application_id: str):
    try:
        app = db.applications.find_one({"_id": ObjectId(application_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid application ID format")
    if app:
        app["_id"] = str(app["_id"])
        return app
    raise HTTPException(status_code=404, detail="Application not found")

@app.get("/applications", response_model=List[Application])
async def list_user_applications(user_id: Optional[str] = None):
    query = {}
    print("User id passed", user_id)
    if user_id:
        query["user_id"] = user_id
    applications = db.applications.find(query)
    return [
        {**app, "_id": str(app["_id"])}  # Convert ObjectId to string
        for app in applications
    ]





# @app.get("/users", response_model=List[User])  # Changed endpoint and model
# async def read_users():
#     users = list(db.job.find({}, {'_id': False}))  # Correct collection name
#     return users


import requests

@app.get("/get-my-ip")
def get_my_ip():
    # Query an external service to find the outbound IP
    response = requests.get("https://httpbin.org/ip")
    return {"outbound_ip": response.json()["origin"]}
