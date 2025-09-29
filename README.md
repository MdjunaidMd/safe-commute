#  Safe Commute Planner

A project that helps users plan **safer commuting routes** by using:
- OpenStreetMap data
- Graph algorithms (NetworkX, OSMnx)
- Crowd-sourced reports
- A clean **React + Leaflet frontend** with a **FastAPI backend**

The goal is to provide routes that are not only shortest but also safer for users.

---

# Project Structure

backend/ # FastAPI backend server

safe-commute-frontend/ # React + Leaflet frontend app


---

# Features
- Safe route planning using OpenStreetMap + NetworkX  
- FastAPI backend with REST endpoints  
- Interactive map-based frontend with React + Leaflet  
- GraphML + JSON datasets stored with **Git LFS**  

---

# Tech Stack
- **Frontend**: React.js, Leaflet.js, Axios, CSS  
- **Backend**: FastAPI, Uvicorn, Python  
- **Data**: OpenStreetMap (GraphML), CSV, JSON  
- **Libraries**: NetworkX, OSMnx, Pandas  
- **Version Control**: Git + Git LFS  

---

# Setup Instructions

 -- Clone the Repository --
 
 This project uses **Git LFS** for large files.  
 
Make sure you have [Git LFS](https://git-lfs.github.com/) installed.


git lfs install

git clone https://github.com/MdjunaidMd/safe-commute.git

cd safe-commute


# Backend Setup


cd backend

-- Create virtual environment --

python -m venv venv

-- On Windows --

venv\Scripts\activate

 -- On Mac/Linux --
 
source venv/bin/activate

-- Install dependencies --

pip install -r requirements.txt

-- Run FastAPI server --

uvicorn main:app --reload --port 8000


# Frontend Setup

cd safe-commute-frontend

-- Install dependencies --

npm install

-- Run React app --

npm start



# Notes

Large files (.graphml, .json) are tracked with Git LFS.

If Git LFS is not installed, you will only see pointer text files instead of data.

Always run git lfs install before cloning.

