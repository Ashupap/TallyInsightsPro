import { motion } from 'framer-motion';
import { Package, AlertTriangle, TrendingDown } from 'lucide-react';

const inventoryItems = [
  { id: 1, name: 'Product A', stock: 450, reorder: 200, status: 'good' },
  { id: 2, name: 'Product B', stock: 180, reorder: 200, status: 'low' },
  { id: 3, name: 'Product C', stock: 85, reorder: 100, status: 'critical' },
  { id: 4, name: 'Product D', stock: 320, reorder: 150, status: 'good' },
  { id: 5, name: 'Product E', stock: 95, reorder: 100, status: 'low' },
];

export default function Inventory() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm text-gray-500 mb-1">Total Items</h3>
              <p className="text-3xl font-bold text-gray-800">1,130</p>
            </div>
            <Package className="text-blue-500" size={32} />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm text-gray-500 mb-1">Low Stock</h3>
              <p className="text-3xl font-bold text-orange-600">8</p>
            </div>
            <TrendingDown className="text-orange-500" size={32} />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm text-gray-500 mb-1">Out of Stock</h3>
              <p className="text-3xl font-bold text-red-600">3</p>
            </div>
            <AlertTriangle className="text-red-500" size={32} />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm text-gray-500 mb-1">Total Value</h3>
              <p className="text-3xl font-bold text-gray-800">₹15.2L</p>
            </div>
            <Package className="text-green-500" size={32} />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Stock Status</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Product</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Current Stock</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Reorder Level</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody>
              {inventoryItems.map((item) => (
                <motion.tr
                  key={item.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-3 px-4 text-sm text-gray-800">{item.name}</td>
                  <td className="py-3 px-4 text-sm text-gray-800">{item.stock}</td>
                  <td className="py-3 px-4 text-sm text-gray-500">{item.reorder}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                        item.status === 'good'
                          ? 'bg-green-100 text-green-800'
                          : item.status === 'low'
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {item.status === 'good' ? 'Good' : item.status === 'low' ? 'Low Stock' : 'Critical'}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
