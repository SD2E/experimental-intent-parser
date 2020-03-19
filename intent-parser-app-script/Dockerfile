#Specify base image created from SD2
FROM sd2e/python3:ubuntu17 

#update image with code for application
COPY src /usr/src/app/
RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt

#run app
CMD ["python3", "/usr/src/app/ip_addon_script.py"]
