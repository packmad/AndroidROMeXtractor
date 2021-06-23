FROM python:3.6.8-slim-stretch AS build

RUN apt update && apt install --no-install-recommends -y git build-essential libz-dev

RUN git clone https://github.com/anestisb/android-simg2img.git && \
    cd ./android-simg2img/ && make

RUN git clone https://github.com/packmad/pacextractor.git && \
    cd ./pacextractor/ && make

##########################################################################################

FROM python:3.6.8-slim-stretch

WORKDIR /AndroidSecurityBulletins

# Copy the binaries generated previously.
COPY --from=build /android-simg2img/simg2img /usr/local/bin/
COPY --from=build /pacextractor/pacextractor /usr/local/bin/

# Install the needed tools.
RUN DEBIAN_FRONTEND=noninteractive \
    # Add non-free repository.
    printf "deb http://deb.debian.org/debian stretch main non-free\n\
    deb http://security.debian.org/debian-security stretch/updates main\n\
    deb http://deb.debian.org/debian stretch-updates main\n" > /etc/apt/sources.list && \
    # Python 2 and other prerequisites.
    apt update && apt install --no-install-recommends -y \
    gcc libc6-dev libfuzzy-dev libmagic-dev python2.7 python-pip \
    git curl perl file rar unrar unzip atool brotli dexdump liblz4-tool liblzo2-dev xz-utils bzip2 e2fsprogs unyaffs && \
    # Needed library for Python 2.
    pip2 install --no-cache-dir protobuf && \
    # Download and unpack FlashTool
    curl -sL -o FlashTool.7z https://www.dropbox.com/s/t6xkxgieepox73r/FlashTool.7z?dl=1 && \
    7za x FlashTool.7z -oarx/bin/FlashTool && rm FlashTool.7z && \
    # Clean.
    apt remove --purge -y make patch gnupg curl && \
    apt autoremove --purge -y && apt clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy and install requirements for Python and NodeJS.
COPY ./requirements.txt ./
RUN pip3 install --upgrade pip setuptools
RUN pip3 install --no-cache-dir -r ./requirements.txt

# Copy source code.
COPY ./ ./

# Not needed in Docker, used only for compatibility.
RUN cd ./setuid_wrapper/ && gcc wrapper.c -o wrapper && \
    cp wrapper /usr/local/bin/ && chmod u+s /usr/local/bin/wrapper
