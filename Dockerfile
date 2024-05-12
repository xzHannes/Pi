FROM nginx:alpine
ADD https://raw.githubusercontent.com/xzHannes/Pi/main/index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
