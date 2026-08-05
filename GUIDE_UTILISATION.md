# Guide d'utilisation — Plateforme IA Agent

## 1. Présentation

La plateforme IA Agent permet de créer, configurer et utiliser des agents conversationnels spécialisés sans écrire de code métier. Chaque agent est défini par un simple fichier YAML et un prompt système Markdown. Les agents peuvent interroger une base de connaissances vectorielle, exécuter des outils, et mémoriser l'historique des conversations.

## 2. Prérequis

- Python 3.12
- Clé API OpenAI
- Docker et Docker Compose (recommandé pour la fonctionnalité RAG complète)

## 3. Installation

### 3.1. Cloner le projet

```bash
git clone <url-du-depot>
cd ai-agents
```

### 3.2. Créer le fichier d'environnement

```bash
cp .env.example .env
```

Éditer `.env` et renseigner au minimum :

```env
OPENAI_API_KEY=sk-votre-cle-api
DATABASE_URL=sqlite:///./data/agent_platform.db
```

### 3.3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3.4. Initialiser la base de données

```bash
python scripts/init_db.py
```

## 4. Démarrage de l'application

### 4.1. Démarrer le backend

```bash
uvicorn app.api.v1.app:app --host 0.0.0.0 --port 8000 --reload
```

Le backend sera accessible sur `http://localhost:8000`.

- Documentation interactive Swagger : `http://localhost:8000/docs`
- Documentation ReDoc : `http://localhost:8000/redoc`

### 4.2. Démarrer le frontend

Dans un autre terminal :

```bash
streamlit run app/frontend/streamlit_app.py
```

L'interface sera accessible sur `http://localhost:8501`.

### 4.3. Démarrage avec Docker Compose

```bash
docker-compose up --build
```

- Backend : `http://localhost:8000`
- Frontend : `http://localhost:8501`

## 5. Connexion

L'application utilise une authentification par jetons JWT.

### 5.1. Identifiants par défaut

| Email | Mot de passe |
|-------|--------------|
| admin@example.com | admin123 |

### 5.2. Connexion via le frontend

1. Ouvrir `http://localhost:8501`
2. Saisir l'email et le mot de passe
3. Cliquer sur **Se connecter**

### 5.3. Connexion via l'API

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```

La réponse contient un jeton `access_token` à utiliser dans les en-têtes suivants :

```
Authorization: Bearer <votre-token>
```

## 6. Utilisation du frontend

### 6.1. Sélection d'un agent

La barre latérale liste tous les agents disponibles. Cliquer sur le nom de l'agent pour le sélectionner. Les informations affichées sont :

- Description
- Modèle utilisé
- Outils disponibles

### 6.2. Chat

1. Sélectionner un agent dans la barre latérale
2. Saisir un message dans la zone de texte en bas
3. Appuyer sur **Entrée**

L'assistant répond et affiche les sources s'il a utilisé la recherche documentaire.

### 6.3. Documents

1. Aller dans la section **Documents**
2. Choisir un fichier (PDF, DOCX, TXT, MD)
3. Sélectionner la collection cible
4. Ajuster la taille des chunks et le chevauchement si nécessaire
5. Cliquer sur **Ingérer**

Le document est découpé, indexé et devient interrogeable par l'agent via la recherche sémantique.

### 6.4. Déconnexion

Cliquer sur **Déconnexion** dans la barre latérale.

## 7. Utilisation de l'API

### 7.1. Authentification

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@example.com&password=admin123
```

### 7.2. Chat

```http
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Bonjour, comment puis-je vous aider ?",
  "agent_name": "maintenance",
  "conversation_id": null
}
```

### 7.3. Liste des agents

```http
GET /api/v1/agents
Authorization: Bearer <token>
```

### 7.4. Upload de document

```http
POST /api/v1/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <fichier>
collection_name: default
chunk_size: 1000
chunk_overlap: 200
```

### 7.5. Liste des documents

```http
GET /api/v1/documents?collection_name=default
Authorization: Bearer <token>
```

### 7.6. Santé de l'application

```http
GET /api/v1/health
```

## 8. Gestion des agents

### 8.1. Emplacement des fichiers

Les agents sont stockés dans le dossier `agents/` sous forme de fichiers YAML.

### 8.2. Structure d'un fichier agent

```yaml
name: maintenance
display_name: Maintenance
description: Assistant spécialisé en maintenance industrielle
system_prompt: ./app/prompts/maintenance.md
vector_collection: maintenance
database_tables: []
tools:
  - rag_search
  - sql_query
  - create_pdf
model: gpt-4o
temperature: 0.2
max_tokens: 4000
is_active: true
```

### 8.3. Ajouter un agent

1. Créer un fichier `agents/mon_agent.yaml`
2. Créer le prompt associé dans `app/prompts/mon_agent.md`
3. Redémarrer le backend ou appeler :

```http
POST /api/v1/agents/reload
Authorization: Bearer <token>
```

### 8.4. Prompts système

Les prompts sont stockés en Markdown dans `app/prompts/`. Ils définissent le rôle, le ton, les contraintes et le format de réponse de l'agent.

Exemple minimal :

```markdown
Tu es un assistant spécialisé en maintenance industrielle.
Tu réponds de manière concise et professionnelle.
Tu utilises les outils disponibles pour répondre aux questions.
```

## 9. Recherche documentaire (RAG)

### 9.1. Collections

Chaque agent possède une collection vectorielle par défaut (`vector_collection` dans le YAML). Il est possible d'utiliser d'autres collections lors de l'upload.

### 9.2. Formats supportés

- PDF
- DOCX
- TXT
- Markdown

### 9.3. Paramètres d'ingestion

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| chunk_size | Taille maximale d'un chunk en caractères | 1000 |
| chunk_overlap | Chevauchement entre chunks | 200 |

### 9.4. Interrogation

Lors d'une conversation, si l'agent possède l'outil `rag_search`, il peut interroger la collection vectorielle. Les sources sont retournées dans la réponse.

## 10. Outils disponibles

| Outil | Description | Permissions requises |
|-------|-------------|----------------------|
| `rag_search` | Recherche sémantique dans une collection | `rag:read` |
| `sql_query` | Exécution de requêtes SQL en lecture seule | `db:read` |
| `send_email` | Envoi d'email | `email:send` |
| `create_pdf` | Génération de PDF | `pdf:create` |
| `search` | Recherche web | `web:search` |
| `calculator` | Calculatrice sécurisée | Aucune |

### 10.1. Activer un outil

Ajouter le nom de l'outil dans la liste `tools` du fichier YAML de l'agent.

```yaml
tools:
  - rag_search
  - calculator
```

### 10.2. Créer un outil personnalisé

1. Créer une classe héritant de `BaseTool` dans `app/tools/`
2. Implémenter la méthode `run()`
3. Enregistrer la classe dans `app/tools/manager.py`
4. L'activer dans le YAML de l'agent

## 11. Modèles et paramètres

### 11.1. Modèles supportés

- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### 11.2. Température

| Valeur | Comportement |
|--------|--------------|
| 0.0 | Réponses déterministes, factuelles |
| 0.7 | Équilibré (défaut) |
| 1.5+ | Réponses créatives, variées |

### 11.3. Max tokens

Contrôle la longueur maximale de la réponse. Valeurs courantes : 1024, 2048, 4000, 8192.

## 12. Sauvegarde et maintenance

### 12.1. Base de données

Le fichier SQLite est stocké dans `./data/agent_platform.db`. Pour sauvegarder :

```bash
cp ./data/agent_platform.db ./backups/agent_platform.db.bak
```

### 12.2. Données vectorielles

ChromaDB stocke les données dans `./data/chroma/`. Pour réinitialiser :

```bash
rm -rf ./data/chroma/*
```

### 12.3. Logs

Les logs sont disponibles dans `./logs/app.log`.

## 13. Dépannage

### 13.1. Erreur de connexion à la base de données

Vérifier que le fichier `data/agent_platform.db` existe et que les permissions sont correctes.

### 13.2. Erreur ChromaDB sur Windows

ChromaDB nécessite une compilation C++. Utiliser Docker Compose pour un environnement Linux.

### 13.3. Erreur d'authentification

Vérifier que le jeton JWT n'a pas expiré (durée par défaut : 60 minutes). Se reconnecter si nécessaire.

### 13.4. L'agent ne trouve pas de documents

Vérifier que :
- Le document a été ingéré avec succès
- La collection correspond à celle de l'agent
- L'outil `rag_search` est activé dans le YAML

### 13.5. Erreur 422 lors de l'appel API

Vérifier le format des champs obligatoires dans le corps de la requête. Consulter le schéma dans `/docs`.

## 14. Glossaire

| Terme | Définition |
|-------|------------|
| Agent | Entité conversationnelle configurée par YAML |
| Collection | Espace de stockage vectoriel pour un agent |
| Chunk | Segment de texte issu du découpage d'un document |
| RAG | Recherche Augmentée par Génération |
| Tool | Outil métier exécutable par un agent |
| YAML | Format de configuration des agents |

## 15. Support

Pour toute question ou problème, consulter le README.md principal du projet.
