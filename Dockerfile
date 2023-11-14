FROM public.ecr.aws/sam/build-python3.11

# Install libxml2 and libxslt development packages
RUN yum install -y libxml2-devel libxslt-devel

# Set the work directory
WORKDIR /var/task

# Copy only the required application files and requirements
COPY requirements.txt .

# Install the Python packages into the python/ directory
RUN pip install -r requirements.txt -t python/

# Copy the application directory
COPY app/ app/

# Package everything into a zip file
RUN zip -r lambda-deployment-package.zip python/ app/
