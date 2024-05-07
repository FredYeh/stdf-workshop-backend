const dayjs = require('dayjs')
const dateFormat = () => dayjs(Date.now()).locale('zh-tw').format('YYYY-MM-DD HH:mm:ss')
const outputFormat = () => dayjs(Date.now()).locale('zh-tw').format('MMDDHHmmss')
const codeFormat = () => dayjs(Date.now()).locale('zh-tw').format('YYMMDD')

module.exports = {
  dateFormat,
  outputFormat,
  codeFormat
}
