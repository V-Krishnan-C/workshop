import { useState } from "react";

export default function Create() {
  const [fileName, setFileName] = useState("");
  const [image, setImage] = useState(null);
  const [imageText, setImageText] = useState("");
  const [tempImageId, setTempImageId] = useState("");
  const [success, setSuccess] = useState(false);
  const [content, setContent] = useState({
    title: "",
    content: "",
    tags: [],
  });

  const handleUpload = async (e) => {
    if (e.target.files) {
      let file = e.target.files[0];
      console.log(file);
      console.log(file.name);
      setFileName(file.name);
      setImage(URL.createObjectURL(file));
      console.log("Uploading file...");

      const formData = new FormData();
      formData.append("image", file);

      try {
        const result = await fetch("http://localhost:8001/api/v1/image", {
          method: "POST",
          body: formData,
        });

        const data = await result.json();
        let temp_image_id = data["temp_image_id"];
        let caption = data["caption"];

        setTempImageId(temp_image_id);

        setImageText(caption);
      } catch (error) {
        console.error(error);
      }
    }
  };

  let handleGenerate = async () => {
    let url = new URL("http://localhost:8001/api/v1/generate");
    let params = { caption: imageText };
    url.search = new URLSearchParams(params).toString();
    const result = await fetch(url, {
      method: "POST",
    });

    const data = await result.json();
    console.log(data);
    setContent(data);
  };

  let handleSave = async () => {
    let url = new URL("http://localhost:8001/api/v1/products");
    let params = { temp_image_id: tempImageId };
    url.search = new URLSearchParams(params).toString();
    console.log("CONTENT");
    console.log(content);
    let result = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(content),
    });

    result = await result.json();

    if (result["product_id"]) {
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setFileName("");
        setImage(null);
        setImageText("");
        setTempImageId("");
        setContent({
          title: "",
          content: "",
          tags: [],
        });
      }, 4000);
    }
  };

  return (
    <div className="h-full flex flex-row font-semibold">
      <div className="bg-base-300 rounded-box flex flex-col p-10 gap-10 w-1/4 flex-none ">
        <div>
          <p className="py-5">Upload your product image</p>
          <input
            type="file"
            name={fileName}
            onChange={handleUpload}
            className="file-input w-full"
          />
          {image != null && (
            <>
              <div className="w-full flex justify-center my-10 rounded-box overflow-hidden">
                <img className="h-45" src={image} />
              </div>
              <input
                type="text"
                placeholder="Image description"
                className="input w-full"
                value={imageText}
                onChange={(e) => setImageText(e.target.value)}
              />
              <button className="btn w-32 mt-10" onClick={handleGenerate}>
                GENERATE
              </button>
            </>
          )}
        </div>
      </div>
      <div className="divider lg:divider-horizontal"></div>
      <div className="bg-base-300 rounded-box flex-1 p-10 flex flex-col gap-10">
        <div>
          <p className="my-5">Title</p>
          <input
            type="text"
            placeholder="Content Title"
            className="input w-full"
            value={content.title}
          />
        </div>
        <div>
          <p className="my-5">Product Description</p>
          <textarea
            className="textarea w-full h-20 overflow-y-scroll"
            placeholder="Product Description"
            value={content.content}
          ></textarea>
        </div>

        <div>
          {content.tags.length > 0 && <p className="my-5">Tags</p>}
          {content.tags.map((tag) => {
            return <div className="badge badge-outline mr-2">{tag}</div>;
          })}
        </div>
        <button className="btn w-32" onClick={handleSave}>
          SAVE
        </button>
      </div>
      {success && (
        <div className="toast m-20 rounded-box">
          <div className="alert alert-info bg-emerald-500">
            <span>New message arrived.</span>
          </div>
        </div>
      )}
    </div>
  );
}
