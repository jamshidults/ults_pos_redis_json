# Installing Redis on Ubuntu

This guide will walk you through the steps to install and configure Redis on an Ubuntu system.

## Prerequisites

- An Ubuntu system (e.g., Ubuntu 20.04 or later)
- A user account with `sudo` privileges

## Installation Steps

1. **Add the Redis Stack repository:s**

   ```bash
    curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

2. **Update your package list and install Redis**

   Begin by updating your package list to ensure you have the latest version information. Then, install the Redis server package:

   ```bash
    sudo apt-get update
    sudo apt-get install redis-stack-server

3. **Start the Redis server**
   ```bash
   sudo systemctl start redis-stack-server

4. **Enable Redis to start on boot**

     ```bash
     sudo systemctl enable redis-stack-server
5. **Install PIP packages**
      ```bash
      pip install redis
      pip install rejson
   
