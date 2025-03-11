import { useState } from "react";
import { products as products_store } from "../state";

export default function Search() {
  const [input, setInput] = useState("");
  const [answer, setAnswer] = useState();
  const [fileName, setFileName] = useState("");
  const [searchType, setSearchType] = useState({
    isText: true,
    imagePath: "",
  });

  let searchProducts = async () => {
    let url = new URL("http://localhost:8001/api/v1/search");
    let params = { query: input };
    url.search = new URLSearchParams(params).toString();
    setInput("");
    let products = await fetch(url);
    products = await products.json();
    setAnswer(products.answer);
    products_store.set(products.products);
  };

  let handleKeyDown = async (e) => {
    if (e.key == "Enter") {
      if (input !== "") {
        setSearchType({
          isText: true,
          imagePath: null,
        });
        await searchProducts();
      }
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files) {
      let file = e.target.files[0];
      console.log(file);
      console.log(file.name);
      setFileName(file.name);
      setSearchType({
        isText: false,
        imagePath: URL.createObjectURL(file),
      });

      console.log("Uploading file...");

      const formData = new FormData();
      formData.append("image", file);

      try {
        const result = await fetch(
          "http://localhost:8001/api/v1/image_search",
          {
            method: "POST",
            body: formData,
          }
        );

        const data = await result.json();

        products_store.set(data);
      } catch (error) {
        console.error(error);
      }
    }
  };

  return (
    <>
      <label className="input">
        <svg
          className="h-[1em] opacity-50"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
        >
          <g
            stroke-linejoin="round"
            stroke-linecap="round"
            stroke-width="2.5"
            fill="none"
            stroke="currentColor"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.3-4.3"></path>
          </g>
        </svg>
        <input
          value={input}
          type="search"
          required
          placeholder="Search"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </label>
      <input
        type="file"
        class="file-input"
        name={fileName}
        onChange={handleFileChange}
      />
      <p className="text-left">LLM Answer:</p>
      <div className="card w-full px-5 text-center">
        {searchType.isText ? (
          answer || "How can I help you?"
        ) : (
          <img className="rounded-box" src={searchType.imagePath} />
        )}
      </div>
    </>
  );
}
