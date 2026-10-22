# River Flow Pipeline

## INTRO

### WHY AM I

A fun project to gather river data to help KAYAKERS decide if they want to go down and paddle. It can also be repurposed by anyone who wants to gather and collect river data from USGS.

### WHAT AM I

- Get USGS water data readings from various monitor locations
- Store them in a local database (SQLite or PostgreSQL)
- Automate the process

### HOW AM I

**2 data sets**, either in SQLite, PostgreSQL, or local JSON files:

- One for the monitor locations
- One to store the readings

**API call** using Python

**Automated** through systemd (Linux Users Only)

**Config file** to hold your user-specific details

**requirements.txt file** to install the needed python modules

---

## REQUIREMENTS

- Linux with systemd (tested on Ubuntu 26.04)
- Python 3.x
- pip (to install the packages in requirements.txt)
- An internet connection (for the USGS API)
- PostgreSQL (only if you choose it over SQLite or JSON)

---

## BACKGROUND INFO

### Key Terms

- **Monitor Location:** A USGS gauge at a specific spot on a river that measures things like flow.
- **USGS:** The United States Geological Survey, the federal agency that publishes the water data.
- **latest-continuous:** The USGS API endpoint that returns the most recent reading for a monitor location.
- **continuous:** The USGS API endpoint that returns a series of readings over a time range. (Planned.)
- **CFS:** Cubic feet per second, the unit used to measure how much water is flowing.

### Timing

Times are in UTC.

---

## WALKTHROUGH SECTIONS



### PREP: Setup Virtual Environments & install Python Packages

---

#### Check That Python 3 Is Installed

1. **Check your Python version:**

       python3 --version

   You should see something like `Python 3.12.3`. If so, you can move on to the next section.

2. **If it is NOT installed** (you'll see `command not found`), install it with:

       sudo apt install python3



#### Create a Virtual Environment (.venv)

Creating a virtual environment is a common best practice.
It keeps this project's Python packages separate from the rest of your system, which prevents conflicts between Python projects.

See the [Python venv documentation](https://docs.python.org/3/tutorial/venv.html) for more on why and how to use virtual environments.

1. **Verify that venv support is installed:**

       python3 -c "import ensurepip; print('venv support is installed')"

   If you see `venv support is installed`, skip to step 3.

2. **If it is NOT installed** (you'll see a `ModuleNotFoundError`), install it with:

       sudo apt install python3-venv

3. **From inside this project folder, create the virtual environment:**

       python3 -m venv .venv

   Keep the name `.venv`, so the `.gitignore` works as intended.

4. **Activate it:**

       source .venv/bin/activate

   Your terminal prompt will show `(.venv)` when it's active.



#### Install Required Python Packages

1. **Make sure the virtual environment is active.** Your terminal prompt should show `(.venv)`. If it doesn't, see the instructions above.

2. **Check that `pip` is installed:**

       pip --version

   You should see a version number, with a path that includes `.venv`.

3. **If `pip` is not installed**, install it with:

       python3 -m ensurepip --upgrade

   Then run `pip --version` again to confirm.

4. **Install the required packages:**

       pip install -r requirements.txt

---

### INITIALIZE: Setup Database Tables & Upload Monitors

This project can use either a SQLite or a PostgreSQL database. Creating a PostgreSQL database is beyond the scope of this project. This project has been tested and is compatible with a PostgreSQL database.

#### Check the .gitignore file 

NOTE: the `.gitignore` file packaged with this repo comes with the following line:

```
# ignore the .env configuration
.env
```

PLEASE CHECK THAT LINE HAS REMAINED UNCHANGED TO PROTECT SENSITIVE INFORMATION SUCH AS PASSWORDS AND IP ADDRESSES PLACED INTO THE `.env`.

#### Create .env File from template 

**NOTE: The `.env` you create in this step must be named EXACTLY `.env`. No more, no less.**

**PostgreSQL Version** 

*If you are using PostgreSQL, you must have created the target server and database previously.*
*PostgreSQL database administration is beyond the scope of this project.*

1. Make a copy of `.env.example_postgresql` and name it `.env`
2. Fill in the database connection parameters requested in the `.env`. *Note: leave the variable DB_TYPE unchanged*

**SQLite Version** 

1. Make a copy of `.env.example_sqlite` and name it `.env`
2. (Optional) You may customize the database name or location if desired. *Note: leave the variable DB_TYPE unchanged*

If a name and location are not specified, the database will be placed inside this repo and will be named `kayaking.db` by default.

#### Update monitors_to_upload.json 

*Holding this space open for instructions not yet written*



#### Run db_initialize.py to setup & initialize required tables 

From your virtual environment, run:

```
python db_initialize.py
```

**What this does**

In **SQLite** this will:
- Create the database
- Create the table `rivers_monitoring_locations` and upsert any `monitors_to_upload.json` entries
- Create the table `rivers_river_readings`

In **PostgreSQL** this will:
- Create the schema `rivers`
- Create the table `rivers.monitoring_locations` and upsert any `monitors_to_upload.json` entries
- Create the table `rivers.river_readings`

---

