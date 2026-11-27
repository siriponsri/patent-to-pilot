"""Native-score review queues with grouped ties and weighted drug histories."""
import numpy as np


METRICS = ("recall20", "precision20", "average_precision", "decision_loss")


def _descending_bins(scores):
    levels, ascending = np.unique(scores, return_inverse=True)
    return len(levels) - 1 - ascending


class ReviewQueue:
    def __init__(self, scores, cutoffs):
        scores, cutoffs = np.asarray(scores), np.asarray(cutoffs)
        self.bins = _descending_bins(scores)
        self.by_cutoff = []
        for cutoff in np.unique(cutoffs):
            rows = np.flatnonzero(cutoffs == cutoff)
            self.by_cutoff.append((rows, _descending_bins(scores[rows])))

    def allocation(self, weights):
        fractions = np.zeros(len(weights))
        slots = 0
        for rows, bins in self.by_cutoff:
            sizes = np.bincount(bins, weights=weights[rows])
            capacity = int(sizes.sum()) // 5
            preceding = sizes.cumsum() - sizes
            tie_fractions = np.clip(capacity - preceding, 0, sizes) / np.maximum(sizes, 1)
            fractions[rows] = tie_fractions[bins]
            slots += capacity
        return fractions, slots

    def measure(self, labels, losses, weights):
        positives = weights * labels
        events = positives.sum()
        fractions, slots = self.allocation(weights)
        captured = positives @ fractions
        sizes = np.bincount(self.bins, weights=weights)
        hits = np.bincount(self.bins, weights=positives)
        precision = hits.cumsum() / np.maximum(1, sizes.cumsum())
        return np.array([captured / events if events else np.nan,
                         captured / slots if slots else np.nan,
                         hits @ precision / events if events else np.nan,
                         weights @ losses / weights.sum()])

    def distinct_event_drugs(self, labels, drug_ids, weights):
        fractions, _ = self.allocation(weights)
        events = labels == 1
        missed = np.ones(int(drug_ids.max()) + 1)
        np.multiply.at(missed, drug_ids[events], 1 - fractions[events])
        return float((1 - missed).sum())
