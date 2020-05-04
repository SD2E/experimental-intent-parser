#Specify base image created from SD2
FROM sd2e/python3:ubuntu17 

ENV PYTHONPATH /usr/src
WORKDIR ${PYTHONPATH} 

#update image with code for application
COPY . $PYTHONPATH
RUN pip3 install --no-cache-dir -r $PYTHONPATH/intent_parser/requirements.txt
RUN pip3 install -e $PYTHONPATH/intent_parser 

#run app
CMD ["intent_parser.addons.ip_addon_script"]
