// pm2 config for the question-map API. Adjust the paths, then:
//   pm2 start ecosystem.config.js && pm2 save
module.exports = {
  apps: [
    {
      name: "mytorah-api",
      cwd: __dirname,
      script: "/path/to/venv/bin/uvicorn",
      args: "server:app --host 127.0.0.1 --port 8001",
      interpreter: "none", // uvicorn is a Python script, not Node
      watch: false, // a restart would kill running generation jobs
      env: {
        MAX_PARALLEL_JOBS: "2",
        MAX_NEW_PER_DAY: "200",
      },
    },
  ],
};
