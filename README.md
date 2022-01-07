
# Visionect 

Looking at displaying some fun things on my Visionect eInk display.

## Getting started

In the below if your default 'python' is python3 then change the below commands to just be 'python'.

1. Install necessary prerequisites
   ```
   sudo apt install -y python3
   python3 -m pip install --user --upgrade pip
   python3 -m pip install --user virtualenv
   
   sudo apt-get install -y wamerican
   ```
1. Create a new virtual environment within the same directory as the git checkout.
   ```
   cd Visionect
   python3 -m virtualenv --python=python3 env
   ```
1. Activate the new virtual environment
   ```
   source env/bin/activate
   ```
   or 
   ```
   env\scripts\activate.bat
   ```
   if you are on windows.
1. Install, into the new virtual environment, the required python modules for this specific environment.  This will be installed within the virtual env which was activated earlier.
   ```
   python3 -m pip install -r requirements.txt
   ```
1. Run the Visionect server process locally.  There is a bunch of confusing installation instructions but there is a super simple one where you installer docker and then docker compose and run a single command that works very well.  Instructions can be found https://support.getjoan.com/hc/en-us/articles/360008822260-How-to-install-the-Visionect-Software-Suite-without-the-VM.  
1. Go to the Visionect server and generate an API Key and Secret.  If you followed the prior instruction then go to http://localhost:8081/ click on 'Users' on the left and then 'Add  new API Key' at the bottom.  
1. Change your device to connect directly to your new server process.  Do this using the Visionect configurator.  https://docs.visionect.com/DeviceConfiguration/UsingVisionectConfigurator.html
1. Create a .env file in the root directory of the project.  It should look something like this:
   ```
   VisionectServer=http://localhost:8081/
   VisionectApiKey=9fbcffffff1f724d5f
   VisionectApiSecret=[Whatever]
   VisionectUUID=[Your UUID]
   ```
   The visionect UUID can be found in the configurator.  Alternatively, once you hook up the device to your server then the server shows your device and its UUID.
1. Finally, start the server process here
   ```
   python3 app.py
   ```
   Do not run the flask webserver using the flask executable - this won't pick up the necessary dependencies and you will be forced to install the requirements outside of the virtual env as well as inside of it.

## Using the server

The server process uses yfinance to gather financial information for some of the default views.  See https://github.com/ranaroussi/yfinance for details.

Once the server process is running then you can connect to it either locally or from another machine.  

You can view the pages produced in a web browser.  For example http://localhost:5000/hello.  If you want to push this to your device then just prepend the path portion of the URL with 'push' - like this http://localhost:5000/push/hello.

