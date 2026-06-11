import { NavLink } from "react-router-dom";

function Navbar() {
  const linkStyle = ({ isActive }) =>
    `text-sm font-medium transition-colors ${
      isActive
        ? "text-blue-600 font-bold"
        : "text-gray-600 hover:text-blue-500"
    }`;

  return (
    <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-200 bg-white shadow-sm">
      <span className="text-lg font-bold text-blue-600">
        DocProcessor
      </span>
      <div className="flex items-center gap-6">
        <NavLink to="/" end className={linkStyle}>Upload</NavLink>
        <NavLink to="/documents" className={linkStyle}>Documents</NavLink>
        <NavLink to="/compare" className={linkStyle}>Compare</NavLink>
      </div>
    </nav>
  );
}

export default Navbar;