export default function Card({ id, title, content, image_uri, tags }) {
  return (
    <div
      onClick={() => {
        window.location.href = "/products/" + id;
      }}
      className="card bg-base-100 shadow-sm"
    >
      <figure>
        <img className="h-56 object-cover" src={image_uri} />
      </figure>
      <div className="card-body">
        <h2 className="card-title">
          {title}
          {Math.random() < 0.34 && (
            <div className="badge badge-secondary">NEW</div>
          )}
        </h2>
        <p className="my-5">{content.slice(0, 200) + "..."}</p>
        <div className="card-actions justify-end">
          {tags.slice(0, 3).map((tag) => {
            return <div className="badge badge-outline">{tag}</div>;
          })}
        </div>
      </div>
    </div>
  );
}
