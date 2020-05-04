# Use an official Python runtime as a parent image
FROM sd2e/python3-pysbol:0.0.5

# Install any needed packages specified in requirements.txt
ENV PYTHONPATH /usr/src
WORKDIR ${PYTHONPATH}
COPY . $PYTHONPATH
 
RUN pip3 install --no-cache-dir -r $PYTHONPATH/intent_parser/requirements.txt
RUN mkdir -p $PYTHONPATH/logs
RUN mv $PYTHONPATH/intent_parser/docker_logging.json logging.json
RUN cp $PYTHONPATH/intent_parser/.transcriptic ~/.transcriptic

# Define environment variables for config
ENV PORT 8080
ENV DICT_ID 1oLJTTydL_5YPyk-wY-dspjIw_bPZ3oCiWiK0xtG8t3g
ENV COLLECTION https://hub.sd2e.org/user/sd2e/design/design_collection/1
ENV SBH_URL https://hub.sd2e.org

# ENV that need to be passed in
#ENV AUTHN 
#ENV SBH_PASSWORD

# Make port available to the world outside this container
EXPOSE $PORT

# Run app.py when the container launches
CMD echo "Port: ${PORT}" && echo "SBH URL: ${SBH_URL}" && echo "COLLECTION: ${COLLECTION}" && intent_parser_server --username sd2e -p $SBH_PASSWORD -s $SBH_URL -l $PORT -c $COLLECTION -i $DICT_ID -a $AUTHN 

