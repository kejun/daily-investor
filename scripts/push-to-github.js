#!/usr/bin/env node
/**
 * Push to GitHub script - using curl
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';
const REPO_OWNER = 'kejun';
const REPO_NAME = 'daily-investor';

function createBlob(content) {
  const cmd = `curl -s -X POST -H "Authorization: token ${GITHUB_TOKEN}" -H "Content-Type: application/json" --data-binary "{\\"content\\":\\"${Buffer.from(content).toString('base64').replace(/"/g, '\\\\"')}\\",\\"encoding\\":\\"base64\\"}" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/git/blobs"`;
  const result = execSync(cmd, { encoding: 'utf8' });
  const match = result.match(/"sha":"([^"]+)"/);
  return match ? match[1] : null;
}

function createTree(files) {
  const tree = files.map(f => ({
    path: f.path,
    mode: '100644',
    type: 'blob',
    sha: f.sha
  }));

  const jsonTree = JSON.stringify(tree).replace(/"/g, '\\"');
  const cmd = `curl -s -X POST -H "Authorization: token ${GITHUB_TOKEN}" -H "Content-Type: application/json" --data-binary "{\\"tree\\":${jsonTree}}" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/git/trees"`;
  const result = execSync(cmd, { encoding: 'utf8' });
  const match = result.match(/"sha":"([^"]+)"/);
  return match ? match[1] : null;
}

function createCommit(treeSha, message) {
  const cmd = `curl -s -X POST -H "Authorization: token ${GITHUB_TOKEN}" -H "Content-Type: application/json" --data-binary "{\\"message\\":\\"${message}\\",\\"tree\\":\\"${treeSha}\\",\\"parents\\":[]}" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/git/commits"`;
  const result = execSync(cmd, { encoding: 'utf8' });
  const match = result.match(/"sha":"([^"]+)"/);
  return match ? match[1] : null;
}

function updateBranch(commitSha) {
  const cmd = `curl -s -X PATCH -H "Authorization: token ${GITHUB_TOKEN}" -H "Content-Type: application/json" --data-binary "{\\"sha\\":\\"${commitSha}\\",\\"force\\":true}" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/git/refs/heads/main"`;
  execSync(cmd, { encoding: 'utf8' });
}

async function main() {
  const baseDir = __dirname.replace('/scripts', '');

  const files = [
    { path: 'README.md', filePath: path.join(baseDir, 'README.md') },
    { path: 'templates/investor-template.md', filePath: path.join(baseDir, 'templates/investor-template.md') },
    { path: 'scripts/daily-invest.js', filePath: path.join(baseDir, 'scripts/daily-invest.js') },
    { path: '2026/02/2026-02-15.md', filePath: path.join(baseDir, '2026/02/2026-02-15.md') }
  ];

  console.log('📤 Pushing to GitHub...\n');

  // Create blobs
  const fileBlobs = [];
  for (const file of files) {
    const content = fs.readFileSync(file.filePath, 'utf8');
    const sha = createBlob(content);
    fileBlobs.push({ path: file.path, sha });
    console.log(`✅ ${file.path}: ${sha.substring(0, 7)}`);
  }

  console.log('\n🌳 Creating tree...');
  const treeSha = createTree(fileBlobs);
  console.log(`✅ Tree: ${treeSha.substring(0, 7)}`);

  console.log('\n📝 Creating commit...');
  const commitSha = createCommit(treeSha, 'Initial commit: 每日投资洞察系统 (2026-02-15)');
  console.log(`✅ Commit: ${commitSha.substring(0, 7)}`);

  console.log('\n🔄 Updating main branch...');
  updateBranch(commitSha);
  console.log('✅ Done!');

  console.log(`\n🔗 https://github.com/${REPO_OWNER}/${REPO_NAME}`);
}

main().catch(console.error);
