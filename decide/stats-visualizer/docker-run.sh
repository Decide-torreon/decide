docker run \
  -it \
  --rm \
  -v ${PWD}:/app \
  -v /app/node_modules \
  -p 3000:3000 \
  decide_stats_visualizer
