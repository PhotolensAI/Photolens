# Backend

## Getting the api started locally
Clone the repo to run the api locally. And get the packages. Setting up a venv is recommended.
```bash
git clone https://github.com/PhotolensAI/Photolens.git

pip install -r backend/requirements.txt
```

### Enviorment
You have to have a `.env` in backend/ that will include:
 - Api keys for OpenAI, Replicate, HuggingFace
 - Api key, private key, private key id

Also, you have to modify the `firebase_sdk_secret.json` to access to your own database

*When you are done, dont forget to make the filename .env instead of enviorment.env*

### Launching the api.
To run the api in `localhost`, use:
```bash
python app.py
```

*Note: When running with `python` command uses a development server. Do not use it in a production deployment. Use a production WSGI server instead when running the api.*
