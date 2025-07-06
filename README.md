# dungeonchurch-oracle
This repo creates a D3 network visualization of the relationships in the Dungeon Church lore wiki.

# To Do
Use `OUTLINE_API_TOKEN` and `OUTLINE_URL`

1. Download a backup of wiki data
   1. Make API call to start [export of all collections](https://www.getoutline.com/developers#tag/collections/post/collections.export_all)
   2. Use the returned `FileOperation` to [track it's progress](https://www.getoutline.com/developers#tag/fileoperations/post/fileOperations.info)
   3. [Retrieve the file](https://www.getoutline.com/developers#tag/fileoperations/post/fileOperations.redirect) when it's ready
   4. [Delete the backup](https://www.getoutline.com/developers#tag/fileoperations/post/fileOperations.delete) file on the server
3. Process that data into a form D3 can use
4. Create the visualization
5. Publish to Github Pages
