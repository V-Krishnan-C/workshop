import Card from "./Card";
import { useEffect } from "react";
import { useStore } from "@nanostores/react";
import { products as products_store } from "../state";

export default function Cards() {
  const $products = useStore(products_store);

  useEffect(() => {
    let handleFetch = async () => {
      let products_data = await fetch("http://localhost:8000/api/v1/homepage");
      products_data = await products_data.json();
      products_store.set(products_data);
    };

    handleFetch();
  }, []);

  return (
    <div className="bg-base-300 rounded-box grid grid-cols-2 overflow-y-scroll gap-4 p-2">
      {Object.values($products).map((product) => {
        return (
          <Card
            key={product.id}
            id={product.id}
            title={product.content.title}
            content={product.content.content}
            tags={product.content.tags}
            image_uri={product.image_uri}
          />
        );
      })}
    </div>
  );
}
