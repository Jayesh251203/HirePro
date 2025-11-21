#include <bits/stdc++.h>
using namespace std;

string make_final_from_counts(array<int,26> cnt) {
    vector<int> odd;
    for(int i=0;i<26;i++) if(cnt[i]&1) odd.push_back(i);
    int rem = max(0, (int)odd.size() - 1);
    for(int i=25;i>=0 && rem>0;i--) {
        if(cnt[i]&1) { cnt[i]--; rem--; }
    }
    string L;
    for(int i=0;i<26;i++) L.append(cnt[i]/2, char('a'+i));
    string M;
    for(int i=0;i<26;i++) if(cnt[i]&1) { M.push_back(char('a'+i)); break; }
    string R = L;
    reverse(R.begin(), R.end());
    return L + M + R;
}

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s1, s2;
    if(!(cin >> s1)) return 0;
    if(!(cin >> s2)) s2 = "";

    array<int,26> cnt1{}, cnt2{};
    for(char c: s1) cnt1[c-'a']++;
    for(char c: s2) cnt2[c-'a']++;

    vector<int> opts1 = {-1}, opts2 = {-1};
    for(int i=0;i<26;i++){
        if(cnt1[i]>0) opts1.push_back(i);
        if(cnt2[i]>0) opts2.push_back(i);
    }

    string best = "";
    for(int c1 : opts1){
        array<int,26> use1{}, tmp1 = cnt1;
        if(c1 != -1){
            tmp1[c1]--;
            use1[c1] = 1;
        }
        for(int i=0;i<26;i++){
            int pairs = tmp1[i]/2;
            use1[i] += pairs*2;
        }

        for(int c2 : opts2){
            array<int,26> use2{}, tmp2 = cnt2;
            if(c2 != -1){
                tmp2[c2]--;
                use2[c2] = 1;
            }
            for(int i=0;i<26;i++){
                int pairs = tmp2[i]/2;
                use2[i] += pairs*2;
            }

            array<int,26> combined{};
            for(int i=0;i<26;i++) combined[i] = use1[i] + use2[i];

            string cand = make_final_from_counts(combined);

            if(cand.size() > best.size() || (cand.size() == best.size() && cand < best)){
                best = cand;
            }
        }
    }

    cout << best << '\n';
    return 0;
}
