# Remna Telegram Bot

A Telegram bot for administering the Remna system, built with TypeScript and the Telegraf framework. The bot provides a convenient interface for managing users, nodes, hosts, subscriptions, and system statistics via Telegram commands, integrating with the Remna API through the `@remnawave/backend-contract` SDK.

## Features

### General Commands
- `/start` - Initializes the bot and displays a welcome message.
- `/help` - Lists all available commands.
- `/login` - Authenticates an administrator using Remna API credentials.
- `/logout` - Ends the administrator's session.
- `/status` - Displays the current status of the Remna system.

### User Management
- `/users` - Lists users with filtering and pagination options.
- `/user_info [username/uuid]` - Shows detailed user information.
- `/user_create` - Creates a new user interactively.
- `/user_update [username/uuid]` - Updates user details.
- `/user_delete [username/uuid]` - Deletes a user.
- `/user_disable [username/uuid]` - Disables a user account.
- `/user_enable [username/uuid]` - Enables a user account.
- `/user_reset_traffic [username/uuid]` - Resets a user's traffic usage.

### Node Management
- `/nodes` - Lists all nodes.
- `/node_info [uuid]` - Displays detailed node information.
- `/node_create` - Creates a new node interactively.
- `/node_update [uuid]` - Updates node details.
- `/node_delete [uuid]` - Deletes a node.
- `/node_restart [uuid]` - Restarts a node.
- `/node_enable [uuid]` - Enables a node.
- `/node_disable [uuid]` - Disables a node.
- `/restart_all_nodes` - Restarts all nodes.

### Host Management
- `/hosts` - Lists all hosts.
- `/host_info [uuid]` - Shows detailed host information.
- `/host_create` - Creates a new host.
- `/host_update [uuid]` - Updates host details.
- `/host_delete [uuid]` - Deletes a host.

### Subscription Management
- `/subscriptions` - Lists all subscriptions.
- `/subscription_info [uuid]` - Displays subscription details.
- `/revoke_subscription [uuid]` - Revokes a subscription.

### Statistics and Monitoring
- `/stats` - Shows overall system statistics.
- `/bandwidth_stats` - Displays bandwidth usage statistics.
- `/node_usage [uuid]` - Shows resource usage for a specific node.
- `/user_usage [uuid]` - Shows resource usage for a specific user.
- `/monitoring` - Provides real-time system monitoring data.
- `/backup` - Creates a system backup (superadmin only).

### Additional Features
- **Notifications**: Sends alerts to a designated Telegram channel for critical events (e.g., node restarts, system errors).
- **Health Checks**: Periodically monitors node health and notifies about high CPU/memory usage or offline nodes.
- **Backups**: Supports creating and managing system backups.
- **Logging**: Comprehensive logging for debugging and monitoring user actions.

## Project Structure

```
remna-telegram-bot/
├── src/
│   ├── index.ts                    # Application entry point
│   ├── config/                     # Configuration files
│   ├── api/                        # API client and service modules
│   ├── bot/                        # Bot initialization and command handlers
│   ├── utils/                      # Utility functions (logging, validation, formatting)
│   ├── types/                      # TypeScript type definitions
├── .env                            # Environment variables
├── .env.example                    # Example environment file
├── Dockerfile                      # Docker configuration
├── docker-compose.yml              # Docker Compose configuration
├── package.json                    # Project dependencies
├── tsconfig.json                   # TypeScript configuration
└── README.md                       # Project documentation
```

## Prerequisites

- Docker (v20.10 or higher)
- Docker Compose (v2.0 or higher)
- A Telegram bot token (obtained from [BotFather](https://t.me/BotFather))
- Access to the Remna API with valid credentials
- (Optional) Prometheus for monitoring integration
- (Optional) A Telegram channel for notifications

## Installation

The bot is deployed using Docker and Docker Compose.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dignezzz/remna-telegram-bot.git
   cd remna-telegram-bot
   ```

2. **Set up environment variables**:
   Copy the `.env.example` file to `.env` and fill in the required values:
   ```env
   BOT_TOKEN=your-telegram-bot-token
   API_URL=https://your-remna-api.com
   NOTIFICATION_CHANNEL_ID=your-telegram-channel-id
   PROMETHEUS_URL=https://your-prometheus-instance.com
   BACKUP_DIR=/app/backups
   ```

3. **Build and run the bot**:
   ```bash
   docker compose up -d --build
   ```

4. **Stop the bot** (if needed):
   ```bash
   docker compose down
   ```

5. **View logs**:
   ```bash
   docker compose logs -f
   ```

## Development

For local development, you can use Docker or run the bot directly with Node.js.

- **Build and run with Docker**:
  ```bash
  docker compose up -d --build
  ```

- **Run tests inside Docker**:
  ```bash
  docker compose run --rm bot npm test
  ```

- **Run with Node.js** (requires Node.js v16+):
  ```bash
  npm install
  npm run build
  npm start
  ```

- **Run in development mode** (Node.js, with auto-restart):
  ```bash
  npm run dev
  ```

- **Lint and format code**:
  ```bash
  npm run lint
  npm run format
  ```

## Testing

The project includes:
- **Unit Tests**: For API client, formatters, and validators.
- **Integration Tests**: For API interactions and command scenarios.
- **End-to-End Tests**: For full bot workflows.

Run tests with:
```bash
docker compose run --rm bot npm test
```

Example test cases are provided in `tests/api/client.test.ts`.

## Dependencies

### Production
- `telegraf`: Telegram bot framework
- `@remnawave/backend-contract`: Remna API SDK
- `axios`: HTTP client
- `winston`: Logging library
- `dotenv`: Environment variable management
- `node-cache`: In-memory caching
- `joi`: Data validation

### Development
- `typescript`: TypeScript compiler
- `ts-node`: TypeScript execution
- `nodemon`: Auto-restart for development
- `jest`: Testing framework
- `eslint`: Code linting
- `prettier`: Code formatting

## Authentication and Authorization

- **Authentication**: Users must run `/login` to provide the Remna API URL and credentials. The bot stores a session token securely.
- **Authorization**: Only superadmins can access sensitive commands (e.g., `/backup`, `/restart_all_nodes`).
- **Session Management**: Tokens are tied to Telegram user IDs and automatically refreshed when expired.

## Error Handling

The bot handles:
- Authentication errors (401)
- Authorization errors (403)
- Network errors
- Validation errors
- Internal server errors

Errors are logged with context and user-friendly messages are sent to the user.

## Logging

- **Levels**: INFO, WARN, ERROR, DEBUG
- **Storage**: Console (development), file (production), optional centralized monitoring
- **Format**: Includes timestamp, user ID, username, command, and result

## CI/CD

The repository includes a GitHub Actions workflow (`.github/workflows/docker-build.yml`) that:
- Builds the Docker image on push to the `main` branch.
- Runs tests inside the container.

The workflow ensures the container builds correctly and passes tests without pushing to a registry.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please follow the code style enforced by ESLint and Prettier.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For issues or feature requests, please open an issue on GitHub or contact the maintainer at [your-email@example.com].
