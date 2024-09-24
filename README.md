# everynyan-moderation-service

This is the source for [everynyan](everynyan.tech)'s auto moderation service. It's a REST API written in FastAPI (Python) and uses the [IBM Max Toxic Comment Classifier](https://github.com/IBM/MAX-Toxic-Comment-Classifier) model to differentiate between toxic and non-toxic comments.

### Run the service

Using pre-built image:
```
docker compose up
```

If you want to build the docker image on your own:
```
git clone https://github.com/shravanasati/everynyan-moderation-service.git
cd ./everynyan-moderation-service

docker build -t yourname/everynyan-moderation-service .
```

Edit the docker compose file to use the image tag you provided.

```
docker compose up
```