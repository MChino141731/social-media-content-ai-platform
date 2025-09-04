function CardItem({ title, imgURL, children }) {
    return (
        <div className="rounded-md bg-zinc-950 hover:scale-105 hover:shadow-xl transition-transform duration-300 cursor-pointer">
            <img src={imgURL} alt={title} className="w-full h-48 object-cover rounded-t-md" />
            <div className="flex flex-col p-4">
                <h2 className="text-white text-2xl font-bold">{title}</h2>
                <p className="text-gray-300">{children}</p>
            </div>
        </div>
    );
}

export default CardItem;