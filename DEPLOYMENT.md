# Guide de déploiement en production

## Prérequis

- Docker 20.10+
- Docker Compose 2.0+
- Domaine configuré avec SSL (HTTPS)
- Clé API OpenAI
- 4 Go de RAM minimum (8 Go recommandé)

## Configuration production

### 1. Variables d'environnement

Créer un fichier `.env.production` :

```env
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=<generate-a-secure-random-key>
DATABASE_URL=sqlite:///./data/agent_platform.db
OPENAI_API_KEY=sk-your-production-key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHROMA_DB_PATH=./data/chroma
JWT_SECRET_KEY=<generate-a-secure-random-key>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
LOG_LEVEL=WARNING
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_CHAT=30/minute
MAX_UPLOAD_SIZE_MB=100
```

### 2. Docker Compose production

Créer `docker-compose.prod.yml` :

```yaml
version: "3.9"

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
    volumes:
      - ./data:/app/data
      - ./agents:/app/agents
      - ./app/prompts:/app/prompts
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "2.0"

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "1.0"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

### 3. Configuration Nginx

Créer `nginx/nginx.conf` :

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:8501;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location /api/v1/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Déploiement

### 1. Cloner le dépôt

```bash
git clone https://github.com/hafedhbouk/ai-agent.git
cd ai-agents
```

### 2. Configurer l'environnement

```bash
cp .env.example .env.production
# Éditer .env.production avec vos valeurs de production
```

### 3. Démarrer

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. Vérifier

```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Monitoring

### Métriques disponibles

| Métrique | Endpoint | Description |
|----------|----------|-------------|
| Santé | `/api/v1/health` | Statut de l'application |
| Agents chargés | `/api/v1/health` | Nombre d'agents actifs |
| Latence chat | Response time | Temps de réponse des agents |
| Tokens utilisés | Chat response | Consommation LLM |

### Logs

Les logs sont disponibles dans `./logs/app.log` et via Docker :

```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Alertes recommandées

- Taux d'erreur > 5%
- Latence > 5 secondes
- Mémoire > 80%
- Disque > 90%

## Sécurité

### Checklist production

- [ ] `APP_SECRET_KEY` est unique et complexe
- [ ] `JWT_SECRET_KEY` est unique et complexe
- [ ] HTTPS configuré avec certificat SSL valide
- [ ] `APP_DEBUG=false`
- [ ] CORS restreint aux domaines autorisés
- [ ] Rate limiting activé
- [ ] Base de données sauvegardée régulièrement
- [ ] Logs rotatifs configurés
- [ ] Firewall configuré
- [ ] Mises à jour automatiques activées

## Sauvegarde

### Base de données

```bash
# Sauvegarde
cp ./data/agent_platform.db ./backups/agent_platform.db.$(date +%Y%m%d)

# Restauration
cp ./backups/agent_platform.db.20260805 ./data/agent_platform.db
```

### Données vectorielles

```bash
# Sauvegarde
tar -czf chroma-backup.tar.gz ./data/chroma/

# Restauration
tar -xzf chroma-backup.tar.gz -C ./data/
```

## Mise à jour

```bash
# Puller les dernières modifications
git pull origin master

# Rebuild et redémarrer
docker-compose -f docker-compose.prod.yml up -d --build
```

## Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs

# Vérifier la configuration
cat .env.production
```

### Erreur de connexion à la base de données

```bash
# Vérifier que le fichier existe
ls -la ./data/agent_platform.db

# Recréer la base si nécessaire
python scripts/init_db.py
```

### Latence élevée

- Vérifier la clé API OpenAI (limites de quota)
- Réduire `max_tokens` dans la config des agents
- Augmenter les ressources Docker
- Vérifier le réseau entre les services

## Scaling

### Horizontal

```yaml
# docker-compose.prod.yml
backend:
  deploy:
    replicas: 3
```

### Vertical

Augmenter les limites de ressources dans `docker-compose.prod.yml` :

```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: "4.0"
```

## Contact

Pour toute question sur le déploiement en production, consulter la documentation technique ou contacter l'équipe de développement.
