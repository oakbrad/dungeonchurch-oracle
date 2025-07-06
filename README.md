# dungeonchurch-oracle
This repo creates a D3 network visualization of the relationships in the Dungeon Church lore wiki.

# To Do
Use `OUTLINE_API_TOKEN` and `OUTLINE_URL`

1. Download a backup of wiki data
   1. Make API call to start [export of all collections](https://www.getoutline.com/developers#tag/collections/post/collections.export_all)
   2. Use the returned `FileOperation` to [track it's progress](https://www.getoutline.com/developers#tag/fileoperations/post/fileOperations.info)
   3. [Retrieve the file](https://www.getoutline.com/developers#tag/fileoperations/post/fileOperations.redirect) when it's ready
   4. [Delete the backup](https://www.getoutline.com/developers#tag/fileoperations/post/fileOperations.delete) file on the server
2. Process that data into a form D3 can use
3. Create the visualization
4. Publish to Github Pages

# Setup

## GitHub Secrets
To use the automated backup workflow, you need to set up the following secrets in your GitHub repository:

1. `OUTLINE_API_TOKEN` - Your Outline API token
   - You can create a new API token in your [Outline account settings](https://app.getoutline.com/settings)
   - Make sure the token has sufficient permissions to export collections

2. `OUTLINE_URL` - The URL of your Outline API
   - Default: `https://app.getoutline.com/api`
   - If you're using a self-hosted Outline instance, use your custom domain

## Automated Backups
The GitHub Action workflow will:
- Run automatically every day at midnight UTC
- Can be triggered manually from the Actions tab in GitHub
- Download a backup of all collections from your Outline wiki
- Save the backup to the `data/` directory
- Commit and push the changes to the repository
