import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { TrendingUp, BarChart3, PieChart, Lock } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [tallyServer, setTallyServer] = useState('http://localhost:9000');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password, tallyServer);

    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.message || 'Login failed');
    }

    setLoading(false);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 flex items-center justify-center p-4">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="w-full max-w-6xl grid md:grid-cols-2 gap-8 items-center"
      >
        <motion.div variants={itemVariants} className="text-white space-y-6">
          <h1 className="text-5xl font-bold mb-4">Tally Prime Analytics</h1>
          <p className="text-xl text-blue-100">
            Your comprehensive business intelligence platform
          </p>

          <div className="space-y-4 mt-8">
            <motion.div
              variants={itemVariants}
              className="flex items-center space-x-4"
            >
              <div className="bg-white/20 p-3 rounded-lg">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold">Real-time Analytics</h3>
                <p className="text-blue-100 text-sm">Live data from Tally Prime with 15+ dashboards</p>
              </div>
            </motion.div>

            <motion.div
              variants={itemVariants}
              className="flex items-center space-x-4"
            >
              <div className="bg-white/20 p-3 rounded-lg">
                <BarChart3 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold">Advanced Insights</h3>
                <p className="text-blue-100 text-sm">AI-powered forecasting and trend analysis</p>
              </div>
            </motion.div>

            <motion.div
              variants={itemVariants}
              className="flex items-center space-x-4"
            >
              <div className="bg-white/20 p-3 rounded-lg">
                <PieChart className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold">Customizable Views</h3>
                <p className="text-blue-100 text-sm">Drag-and-drop tiles with role-based access</p>
              </div>
            </motion.div>
          </div>
        </motion.div>

        <motion.div
          variants={itemVariants}
          className="bg-white rounded-2xl shadow-2xl p-8"
        >
          <div className="flex items-center justify-center mb-6">
            <div className="bg-blue-100 p-3 rounded-full">
              <Lock className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
            Sign In to Your Account
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field"
                placeholder="Enter your username"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="Enter your password"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tally Server URL
              </label>
              <input
                type="text"
                value={tallyServer}
                onChange={(e) => setTallyServer(e.target.value)}
                className="input-field"
                placeholder="http://localhost:9000"
                required
              />
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm"
              >
                {error}
              </motion.div>
            )}

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 text-lg font-semibold disabled:opacity-50"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </motion.button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Demo credentials: Use any username/password to login
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
