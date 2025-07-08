// Auto-generated collection colors

const collectionColors = {
  "ffaa3b03-1b56-4131-aedd-f208a0b3ed03": "#00d084",
  "13b87098-500c-490d-ae46-01356387fe88": "#ffbe0b",
  "9eecd4c7-d708-40ca-add0-5f6ec31066cf": "#0366d6",
  "a60ccdf0-330c-4a08-8511-729aea62ca75": "#9e5cf7",
  "7e8c2f3f-6e08-4b08-b207-33365583a8bf": "#4E5C6E",
  "7275a3d8-27da-4f63-ac39-a9bc9a1ec6d7": "#ffbe0b",
  "184c6e39-ef59-49b4-89d8-302d6abae3cf": "#ff4dfa",
  "28015ad0-50f5-4495-a6c5-2415436a3d40": "#ff825c",
  "7c70ca02-fdd6-4a30-a8b7-931093ebfbd8": "#ff5c80",
  "9870bc72-55da-4158-892c-3c54ec9e5828": null,
  "098323c3-c9a2-45f4-ab12-ff8b759c5be7": "#9e5cf7",
  "77c74010-e20c-419c-8122-97563ec685b6": "#00d084",
  "ac7efc59-549b-4aa9-9ed8-1b22f82382d0": "#FF4DFA"
};

// Function to get color for a collection
function getCollectionColor(collectionId) {
    console.log("getCollectionColor called with:", collectionId);
    console.log("Available colors:", Object.keys(collectionColors));
    return collectionColors[collectionId] || '#69b3a2';
}

