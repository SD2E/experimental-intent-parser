#Specify base image created from SD2
FROM sd2e/python3:ubuntu17 

ENV PYTHONPATH /usr/src/app
WORKDIR ${PYTHONPATH} 

#update image with code for application
COPY src $PYTHONPATH
RUN pip3 install --no-cache-dir -r $PYTHONPATH/requirements.txt


#run app
CMD ["python3", "ip_addon_script.py"]
