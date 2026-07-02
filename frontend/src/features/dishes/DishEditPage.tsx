import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  createDish,
  fetchDish,
  fetchTags,
  updateDish,
  type DishInput,
  type Tag,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { useAuth } from "../auth/AuthContext";

const emptyForm: DishInput = {
  name: "",
  description: "",
  default_servings: null,
  prep_time_minutes: null,
  cook_time_minutes: null,
  difficulty: "",
  active: true,
  notes: "",
  tag_ids: [],
};

export function DishEditPage() {
  const { dishId } = useParams();
  const isNew = !dishId;
  const navigate = useNavigate();
  const { accessToken, isAdmin } = useAuth();
  const [form, setForm] = useState<DishInput>(emptyForm);
  const [tags, setTags] = useState<Tag[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isAdmin) {
      navigate("/dishes", { replace: true });
    }
  }, [isAdmin, navigate]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    fetchTags(accessToken)
      .then(setTags)
      .catch(() => setTags([]));
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken || isNew || !dishId) {
      return;
    }
    let cancelled = false;
    fetchDish(accessToken, Number(dishId))
      .then((dish) => {
        if (!cancelled) {
          setForm({
            name: dish.name,
            description: dish.description,
            default_servings: dish.default_servings,
            prep_time_minutes: dish.prep_time_minutes,
            cook_time_minutes: dish.cook_time_minutes,
            difficulty: dish.difficulty,
            active: dish.active,
            notes: dish.notes,
            tag_ids: dish.tag_ids,
          });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load dish");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, dishId, isNew]);

  function toggleTag(tagId: number) {
    setForm((current) => {
      const selected = new Set(current.tag_ids ?? []);
      if (selected.has(tagId)) {
        selected.delete(tagId);
      } else {
        selected.add(tagId);
      }
      return { ...current, tag_ids: [...selected] };
    });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload: DishInput = {
        ...form,
        description: form.description || null,
        difficulty: form.difficulty || null,
        notes: form.notes || null,
      };
      if (isNew) {
        const created = await createDish(accessToken, payload);
        navigate(`/dishes/${created.id}`);
      } else {
        await updateDish(accessToken, Number(dishId), payload);
        navigate(`/dishes/${dishId}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save dish");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <section className="card">
        <p className="muted">Loading dish…</p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="row-between">
        <h2>{isNew ? "New dish" : "Edit dish"}</h2>
        <Link to={isNew ? "/dishes" : `/dishes/${dishId}`}>Cancel</Link>
      </div>
      <form onSubmit={handleSubmit} className="stack">
        <label>
          Name
          <input
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            required
          />
        </label>
        <label>
          Description
          <textarea
            value={form.description ?? ""}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            rows={3}
          />
        </label>
        <div className="grid-2">
          <label>
            Servings
            <input
              type="number"
              min={1}
              value={form.default_servings ?? ""}
              onChange={(event) =>
                setForm({
                  ...form,
                  default_servings: event.target.value ? Number(event.target.value) : null,
                })
              }
            />
          </label>
          <label>
            Difficulty
            <input
              value={form.difficulty ?? ""}
              onChange={(event) => setForm({ ...form, difficulty: event.target.value })}
            />
          </label>
        </div>
        <fieldset>
          <legend>Tags</legend>
          <div className="tag-grid">
            {tags.map((tag) => (
              <label key={tag.id} className="checkbox-pill">
                <input
                  type="checkbox"
                  checked={(form.tag_ids ?? []).includes(tag.id)}
                  onChange={() => toggleTag(tag.id)}
                />
                {tag.family}: {tag.name}
              </label>
            ))}
          </div>
        </fieldset>
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : "Save dish"}
        </button>
      </form>
    </section>
  );
}
