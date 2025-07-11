FROM nginx:alpine

#COPY . /usr/share/nginx/html

COPY ./css /usr/share/nginx/html/css
COPY ./explorer /usr/share/nginx/html/explorer
COPY ./images /usr/share/nginx/html/images
COPY ./js /usr/share/nginx/html/js
COPY ./portal /usr/share/nginx/html/portal
COPY ./docs /usr/share/nginx/html/docs
COPY ./privacy /usr/share/nginx/html/privacy
COPY ./terms /usr/share/nginx/html/terms
COPY ./index.html /usr/share/nginx/html/index.html

EXPOSE 80