import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="w-full bg-gray-50 border-b border-gray-300 py-4">
      <ul className="flex justify-center gap-10">
        <li>
          <Link to="/" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
            Home
          </Link>
        </li>
        <li>
          <Link to="/contatti" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
            Contact
          </Link>
        </li>
        <li>
          <Link to="/about" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
            About us
          </Link>
        </li>
        <li>
          <Link to="/twitter" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
            Twitter
          </Link>
        </li>
        <li>
          <Link to="/instagram" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
            Instagram
          </Link>
        </li>
        <li>
          <Link to="/product" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
            New Product
          </Link>
        </li>
        <li>
          <Link to="/inci" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
            Check INCI
          </Link>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
