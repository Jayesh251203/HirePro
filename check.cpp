#include <bits/stdc++.h>

using namespace std;

string mergePalindromes(string s1, string s2) {
    // Combine both strings
    string combined = s1 + s2;
    
    // Count frequency of each character
    map<char, int> freq;
    for (char c : combined) {
        freq[c]++;
    }
    
    // Build the palindrome
    string half = "";
    string middle = "";
    
    // Process characters in alphabetical order
    for (auto& p : freq) {
        char c = p.first;
        int count = p.second;
        
        // Add pairs to the half
        for (int i = 0; i < count / 2; i++) {
            half += c;
        }
        
        // If count is odd, keep one for potential middle
        if (count % 2 == 1 && middle.empty()) {
            middle = string(1, c);
        }
    }
    
    // Build the palindrome: half + middle + reverse(half)
    string result = half;
    result += middle;
    
    // Add reversed half
    string reversedHalf = half;
    reverse(reversedHalf.begin(), reversedHalf.end());
    result += reversedHalf;
    
    return result;
}

int main() {
    // Test with provided examples
    string s1, s2;
    cin >> s1 >> s2;
    cout << mergePalindromes(s1, s2) << endl;
    return 0;
}