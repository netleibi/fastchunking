/*
 * An efficient RabinKarp rolling hash implementation.
 *
 * This library is based on and thus includes code fragments of the file
 * rabinkarphash.h of the rollinghashcpp package by Daniel Lemire.
 *
 * License: Apache 2.0
 *
 * The base version is available under
 * https://github.com/lemire/rollinghashcpp/blob/07c597c17df7e0feb877cf5a7f556af9d6d17a83/rabinkarphash.h
 *
 * Author: Dominik Leibenger
 *
 */
#ifndef RABINKARP_H
#define RABINKARP_H

#include <algorithm>
#include "characterhash.h"

#include <cstring>
#include <iostream>
#include <list>

class RabinKarp {
	/* Implementation of the Rabin-Karp hash function.
	 *
	 * This code is based on
	 * https://github.com/lemire/rollinghashcpp/blob/07c597c17df7e0feb877cf5a7f556af9d6d17a83/rabinkarphash.h
	 * and therefore uses some variable names from the source.
	 */
public:
	RabinKarp(int my_window_size, int seed) :
			hasher(maskfnc<uint32>(WORDSIZE), seed),
			HASHMASK(maskfnc<uint32>(WORDSIZE)),
			BtoN(1),
			window_size(my_window_size) {
		for (int i = 0; i < window_size; ++i) {
			BtoN *= B;
			BtoN &= HASHMASK;
		}
	}

protected:
	void _update(unsigned char b, uint32 &hashvalue, unsigned char* window,
			int &window_head, int &window_level) {
		/* Consume a byte and update the hash value accordingly.
		 *
		 * The last window_size consumed bytes are always stored to ease rolling
		 * hash computation.
		 */

		if (window_level != window_size)
			// corresponds to eat() in the original implementation
			hashvalue = (B * hashvalue + hasher.hashvalues[b]) & HASHMASK;
		else
			// corresponds to update() in the original implementation
			hashvalue = (B * hashvalue + hasher.hashvalues[b]
					- BtoN * hasher.hashvalues[window[window_head]]) & HASHMASK;

		// store consumed byte in rolling hash window
		window[window_head] = b;

		if (window_head == window_size - 1)
			window_head = 0;
		else
			window_head += 1;

		if (window_level != window_size)
			window_level += 1;
	}

	uint32 _compute_threshold(double my_threshold) {
		/* resolves a relative threshold (e.g., 0.01 for 1% matching hash
		 * values) to an absolute threshold in the range of actual hash values. */
		return static_cast<uint32>(my_threshold * (HASHMASK + 1));
	}

private:
	int n;
	CharacterHash<uint32, unsigned char> hasher;
	const uint32 HASHMASK;
	uint32 BtoN;
	static const uint32 B = 37;
	static const uint32 WORDSIZE = 29; // compute 29-bit integer hashes

protected:
	int window_size;
};

class RabinKarpHash: RabinKarp {
	/* High-level interface that performs chunking based on the Rabin-Karp
	 * rolling hash scheme.
	 *
	 * This is the interface used by the Python library. */
public:
	RabinKarpHash(int my_window_size, int seed) :
			hashvalue(0), window_level(0), window_head(0), RabinKarp(
					my_window_size, seed) {
		window = (unsigned char*) malloc(window_size * sizeof(unsigned char));
	}

	~RabinKarpHash() {
		free(window);
	}

	void set_threshold(double my_threshold) {
		threshold = _compute_threshold(my_threshold);
	}

	std::list<unsigned int> next_chunk_boundaries(std::string *str,
			unsigned int prepend_bytes) {
		/* On input a Python string, this function computes a Python list object
		 * containing chunk boundary positions. */
		const char* cstr = str->c_str();
		unsigned int len = str->length();

		for (unsigned int i = 0; i < prepend_bytes; ++i)
			update(0);

		std::list<unsigned int> results;
		for (unsigned int i = 0; i < len; ++i) {
			update(cstr[i]);
			if (window_level == window_size && hashvalue < threshold)
				results.push_back(i + 1);
		}
		return (results);
	}

private:
	void update(unsigned char b) {
		_update(b, hashvalue, window, window_head, window_level);
	}

	int window_level;
	int window_head;
	unsigned char* window;

	uint32 threshold;
	uint32 hashvalue;
};

class RabinKarpMultiThresholdHash: RabinKarp {
	/*
	 * Performs multi-level chunking of a given content, based on the thresholds
	 * specified during initialization.
	 *
	 * Chunking is performed as follows:
	 * - To compute chunk boundaries of the first level (i.e., the nodes
	 *   directly under the root node), the content is prepended by
	 *   prepend_bytes bytes (as to allow that the first chunk is smaller than
	 *   the specified window size) and then chunked using Rabin Karp, i.e., a
	 *   chunk boundary is created whenever the current hashvalue is below the
	 *   first given threshold.
	 * - Subsequent levels are computed similarly, but each higher-level chunk
	 *   is considered in isolation, i.e., computed chunk boundaries of a
	 *   level-(i+1) chunk must not depend on content outside of the scope of
	 *   the corresponding level-i chunk. For this reason, a single chunking
	 *   instance is not enough. Instead, we use one chunking instance for each
	 *   individual threshold, filling lower-level windows with zeros whenever a
	 *   chunk boundary at a higher level has been found.
	 */

public:
	RabinKarpMultiThresholdHash(int my_window_size,
								int seed,
								std::list<double> my_thresholds) :
			thresholds_count(my_thresholds.size()),
			thresholds((uint32*) malloc(thresholds_count * sizeof(uint32))),
			least_restrictive_required_chunker_index(0), // initialize optimization code
			RabinKarp(my_window_size, seed) {
		// initialize list of thresholds
		std::list<double>::iterator iter = my_thresholds.begin();
		int i = 0;
		for (std::list<double>::iterator iter = my_thresholds.begin();
				iter != my_thresholds.end(); ++iter) {
			thresholds[i] = _compute_threshold(*iter);
			++i;
		}

		// initialize a chunker for each threshold
		threshold_window_levels = new int[thresholds_count];
		threshold_window_heads = new int[thresholds_count];
		threshold_content_lengths = new int[thresholds_count];
		threshold_hashvalues = new uint32[thresholds_count];
		threshold_windows = new unsigned char*[thresholds_count];
		for (int threshold_index = 0; threshold_index < thresholds_count;
				threshold_index++) {
			threshold_window_levels[threshold_index] = 0;
			threshold_window_heads[threshold_index] = 0;
			threshold_content_lengths[threshold_index] = 0;
			threshold_hashvalues[threshold_index] = 0;
			threshold_windows[threshold_index] = new unsigned char[window_size];
		}
	}

	~RabinKarpMultiThresholdHash() {
		// clean up threshold-specific chunkers
		delete[] threshold_window_levels;
		delete[] threshold_window_heads;
		delete[] threshold_content_lengths;
		delete[] threshold_hashvalues;
		for (int i = 0; i < thresholds_count; i++)
			delete[] threshold_windows[i];
		delete[] threshold_windows;

		// clean up thresholds
		free(thresholds);
	}

	std::list<unsigned int> next_chunk_boundaries_with_thresholds(
			std::string *content, unsigned int prepend_bytes) {
		const char* content_str = content->c_str();
		unsigned int len = content->length();

		// prepend bytes as specified
		for (int threshold_index = 0; threshold_index < thresholds_count;
				++threshold_index)
			for (unsigned int i = 0; i < prepend_bytes; ++i)
				_update(0, threshold_hashvalues[threshold_index],
						threshold_windows[threshold_index],
						threshold_window_heads[threshold_index],
						threshold_window_levels[threshold_index]);

		// process content byte by byte
		std::list<unsigned int> boundaries;
		for (unsigned int i = 0; i < len; ++i) {
			// let current byte be processed by each required chunker
			int new_least_restrictive_required_chunker_index = thresholds_count
					- 1;

			for (int threshold_index = thresholds_count - 1;
					threshold_index >= least_restrictive_required_chunker_index;
					--threshold_index) {
				_update(content_str[i], threshold_hashvalues[threshold_index],
						threshold_windows[threshold_index],
						threshold_window_heads[threshold_index],
						threshold_window_levels[threshold_index]);
				threshold_content_lengths[threshold_index]++;
				if (threshold_content_lengths[threshold_index] < window_size)
					new_least_restrictive_required_chunker_index =
							threshold_index;
			}
			least_restrictive_required_chunker_index =
					new_least_restrictive_required_chunker_index;

			/* assuming that thresholds are ordered from least restrictive to
			 * most restrictive, determine the most restrictive threshold that
			 * matches (if any) */
			int matching_threshold_index = -1;
			for (int threshold_index = 0; threshold_index < thresholds_count;
					++threshold_index) {
				int used_chunker_index = std::max(threshold_index,
						least_restrictive_required_chunker_index);

				/* thresholds are processed in this order since the majority of
				 * all positions will not match any threshold, allowing for an
				 * early break which is only possible when starting with the
				 * least restrictive threshold */
				if (threshold_window_levels[used_chunker_index] == window_size
						&& threshold_hashvalues[used_chunker_index]
								< thresholds[threshold_index]) {
					/* set matching threshold index, which will probably be
					 * overwritten by a higher (i.e., more restrictive threshold
					 * index in a subsequent iteration) */
					matching_threshold_index = threshold_index;
				} else {
					/* if this threshold did not match and if it does not depend
					 * on any prepended zeros, none of the more restrictive
					 * thresholds will match */
					if (threshold_content_lengths[used_chunker_index]
							>= window_size)
						break;
				}
			}

			if (matching_threshold_index != -1) {
				// add found boundary to list of boundaries
				boundaries.push_back(i + 1);
				boundaries.push_back(matching_threshold_index);

				/* reset chunkers for lower-level nodes (i.e., chunkers with
				 * less restrictive thresholds) */
				for (int j = 0; j < matching_threshold_index; ++j) {
					for (unsigned int k = 0; k < prepend_bytes; ++k)
						_update(0, threshold_hashvalues[j],
								threshold_windows[j], threshold_window_heads[j],
								threshold_window_levels[j]);
					threshold_content_lengths[j] = 0;
				}

				/* some chunkers for nodes lower (i.e., chunkers with less
				 * restrictive thresholds) than
				 * least_restrictive_required_chunker_index are now used again
				 * due to the above-described reset, so we update their states
				 * accordingly */
				for (int j = matching_threshold_index;
						j < least_restrictive_required_chunker_index; ++j) {
					threshold_hashvalues[j] =
							threshold_hashvalues[least_restrictive_required_chunker_index];
					std::memcpy(threshold_windows[j],
							threshold_windows[least_restrictive_required_chunker_index],
							window_size);
					threshold_window_heads[j] =
							threshold_window_heads[least_restrictive_required_chunker_index];
					threshold_window_levels[j] =
							threshold_window_levels[least_restrictive_required_chunker_index];
				}
				least_restrictive_required_chunker_index = 0;
			}
		}

		// return boundaries list
		return (boundaries);
	}

private:
	int thresholds_count;
	uint32* thresholds;

	int* threshold_window_levels;
	int* threshold_window_heads;
	int* threshold_content_lengths;
	uint32* threshold_hashvalues;
	unsigned char** threshold_windows;

	/* OPTIMIZATION: If a chunker has processed at least window_size bytes of
	 * the content, all subsequent (i.e., more restrictive threshold) chunkers
	 * would have the same state. Thus, we save redundant executions by
	 * determining the least-restrictive chunker that is still required. */
	int least_restrictive_required_chunker_index;
};

#endif
