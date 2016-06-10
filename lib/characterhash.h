/*
 * This is a modified version of the file characterhash.h within the rollinghashcpp package of Daniel Lemire.
 *
 * License: Apache 2.0
 *
 * The base version is available under
 * https://github.com/lemire/rollinghashcpp/blob/07c597c17df7e0feb877cf5a7f556af9d6d17a83/characterhash.h
 *
 * Modifications:
 * - Allow to specify the seed during initialization of CharacterHash.
 *
 * Author of modifications: Dominik Leibenger
 *
 */
#ifndef CHARACTERHASH
#define CHARACTERHASH

typedef unsigned long long uint64;
typedef unsigned int uint32;
typedef unsigned int uint;

#include <cassert>
#include <iostream>
#include <stdexcept>
#include "mersennetwister.h"

using namespace std;




class mersenneRNG {
 public:
  mersenneRNG(uint32 maxval) : mtr(),n(maxval) {};
  uint32 operator()() { return mtr.randInt(n);} 
  void seed(uint32 seedval) { mtr.seed(seedval);}
  void seed() { mtr.seed();}
  uint32 rand_max() { return n;}
 private:
  MTRand mtr;
  int n;
};

template <typename hashvaluetype>
hashvaluetype maskfnc(int bits) {
    assert(bits>0);
    assert(bits<=sizeof(hashvaluetype)*8);
    hashvaluetype x = static_cast<hashvaluetype>(1) << (bits - 1);
    return x ^ (x - 1);
}

template <typename hashvaluetype = uint32, typename chartype =  unsigned char>
class CharacterHash {
 public:
  CharacterHash(hashvaluetype maxval, uint32 seed) {
    if(sizeof(hashvaluetype) <=4) {
      mersenneRNG randomgenerator(maxval);
      randomgenerator.seed(seed);
  	  for(size_t k =0; k<nbrofchars; ++k) 
  	    hashvalues[k] = static_cast<hashvaluetype>(randomgenerator());
    } else if (sizeof(hashvaluetype) == 8) {
         mersenneRNG randomgenerator(maxval>>32);
         randomgenerator.seed(seed);
         mersenneRNG randomgeneratorbase((maxval>>32) ==0 ? maxval : 0xFFFFFFFFU);
  	     for(size_t k =0; k<nbrofchars; ++k) 
  	        hashvalues[k] = static_cast<hashvaluetype>(randomgeneratorbase()) 
  	           | (static_cast<hashvaluetype>(randomgenerator()) << 32);
  	} else throw runtime_error("unsupported hash value type");
  }

  enum{nbrofchars = 1 << ( sizeof(chartype)*8 )};

  hashvaluetype hashvalues[1 << ( sizeof(chartype)*8 )];	
};

#endif

