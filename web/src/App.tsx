import { Navigate, Route, Routes } from "react-router-dom";
import { useMe } from "@/api/hooks";
import { Layout } from "@/components/Layout";
import { Login } from "@/pages/Login";
import { Library } from "@/pages/Library";
import { Reader } from "@/pages/Reader";
import { Import } from "@/pages/Import";
import { Search } from "@/pages/Search";

function Protected({ children }: { children: JSX.Element }) {
  const { data: me, isLoading } = useMe();
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted">
        <span className="animate-pulse font-serif text-xl">Anthology</span>
      </div>
    );
  }
  if (!me) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <Protected>
            <Layout>
              <Routes>
                <Route path="/" element={<Library />} />
                <Route path="/read/:id" element={<Reader />} />
                <Route path="/import" element={<Import />} />
                <Route path="/search" element={<Search />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </Protected>
        }
      />
    </Routes>
  );
}
