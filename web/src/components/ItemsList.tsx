interface Item {
  vinted_id: string;
  title: string;
  price: number;
  brand: string | null;
  url: string;
  image_url: string | null;
  favorites: number | null;
  market: string;
}

interface ItemsListProps {
  items: Item[];
}

export function ItemsList({ items }: ItemsListProps) {
  if (items.length === 0) {
    return <p className="no-items">No items found</p>;
  }

  return (
    <div className="items-list">
      <h3>Recent Items</h3>
      <div className="items-grid">
        {items.map((item) => (
          <a
            key={item.vinted_id}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="item-card"
          >
            {item.image_url && (
              <img src={item.image_url} alt={item.title} className="item-image" />
            )}
            <div className="item-info">
              <span className="item-title">{item.title}</span>
              <span className="item-brand">{item.brand || item.title}</span>
              <div className="item-meta">
                <span className="item-price">€{item.price.toFixed(2)}</span>
                <span className="item-market">{item.market}</span>
                {item.favorites !== null && (
                  <span className="item-favorites">♥ {item.favorites}</span>
                )}
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
