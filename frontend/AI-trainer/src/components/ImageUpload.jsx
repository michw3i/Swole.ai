import React, { useState, useRef } from 'react';

const ImageUploader = () => {
    const [imageFile, setImageFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileChange = (event) => {
        const file = event.target.files?.[0];
        if (file && file.type.substring(0, 5) === "image") {
            setImageFile(file);
            setPreviewUrl(URL.createObjectURL(file));
        } else {
            setImageFile(null);
            setPreviewUrl(null);
        }
    };

    const handleUpload = async () => {
        if (!imageFile) return;

        const formData = new FormData();
        formData.append("image", imageFile);

        try {
            const reponse = await fetch("", {
                method: "POST",
                body: formData,
        });

            if (response.ok) {
                constole.log("Image uploaded successfully!");
            } else {
                console.error("Upload failed.");
            }
        } catch (error) {
            console.error("Error during upload:", error);
        }
    };

     return (
    <div>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*" // Restrict to image files
        style={{ display: 'none' }} // Hide the default input
      />
      
      {/* Custom button to trigger the hidden file input */}
      <button onClick={() => fileInputRef.current.click()}>
        Select Image
      </button>

      {/* Image Preview */}
      {previewUrl && (
        <div>
          <h3>Preview:</h3>
          <img src={previewUrl} alt="Preview" style={{ maxWidth: '200px', maxHeight: '200px' }} />
        </div>
      )}

      {/* Upload button */}
      <button onClick={handleUpload} disabled={!imageFile}>
        Upload Image
      </button>
    </div>
  );
};

export default ImageUpload;