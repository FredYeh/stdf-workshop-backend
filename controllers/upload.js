const { dateFormat } = require('../utils/format/date')
const formidable = require('formidable')
const path = require('path')
const fse = require('fs-extra')
const logger = require('../utils/logger.js')

const UPLOAD_DIR = path.resolve(__dirname, '..', 'files', 'stdf') // 切片儲存目錄
const CREATE_DIR = path.resolve(__dirname, '..', 'files', 'output') // excel儲存目錄

const pipeStream = (path, writeStream) => {
  // console.log("path",path) // 带後綴路徑
  return new Promise((resolve) => {
    const readStream = fse.createReadStream(path) //讀取文件流返回對象
    readStream.on('end', () => {
      fse.unlinkSync(path) //讀取完畢後刪除當前切片
      resolve()
    })
    readStream.pipe(writeStream) // 管道流pipe  讀取的內容寫入生成文件
  })
}

// 合併切片
const mergeFileChunk = async (filePath, fileHash, size) => {
  const chunkDir = path.resolve(UPLOAD_DIR, fileHash) //文件目录路径
  const chunkPaths = await fse.readdir(chunkDir) //讀取目錄下的所有文件，返回array[]
  // 排序，直接讀取未排序可能會出錯
  chunkPaths.sort((a, b) => a.split('-')[1] - b.split('-')[1])
  console.log('所有切片文件:', chunkPaths)
  await Promise.all(
    // 遍歷array，讀寫每个文件内容，依次覆蓋上一个文件内容，最后生成需要攜帶ext的文件
    chunkPaths.map((chunkPath, index) => {
      return pipeStream(
        path.resolve(chunkDir, chunkPath), // file/stdf/pgm/pgm.zip-0
        // 指定位置創藉可寫流、生成的文件路徑，加ext
        fse.createWriteStream(filePath, {
          start: index * size,
          end: (index + 1) * size
        })
      )
    })
  ).catch((err) => {
    console.log(err) // some coding error in handling happened
  })
  if (fse.existsSync(chunkDir)) {
    await fse.rm(chunkDir, { recursive: true, force: true }) // 合併後刪除切片目錄
  }
  // await new Promise(r => setTimeout(r, 2000))
}

// 返回已上船的的切片名
const createUploadedList = async (fileHash) => {
  return fse.existsSync(path.resolve(UPLOAD_DIR, fileHash)) ? await fse.readdir(path.resolve(UPLOAD_DIR, fileHash)) : []
}

const handleVerify = async (req, res) => {
  const { fileHash, filename } = req.body
  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`) // 加後綴為文件，不加為目錄
  console.log('切片保存路徑:', filePath)
  console.log(`${fse.existsSync(filePath) ? 'path exist' : 'path is not exist'}`)
  logger.log('info', `File ${filename} is handling Verify`)
  // if slice path is not exist , mkdir
  if (fse.existsSync(filePath)) {
    logger.log('info', `File ${filePath} is exists`)
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.json({
      code: 20000,
      msg: 'Success',
      data: JSON.stringify({
        shouldUpload: false,
        date: dateFormat()
      })
    })
  } else {
    logger.log('info', `File ${filePath} is not exists`)
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.json({
      code: 20000,
      msg: 'Success',
      data: JSON.stringify({
        shouldUpload: true,
        uploadedList: await createUploadedList(fileHash),
        date: dateFormat()
      })
    })
  }
}
const handleFormData = async (req, res) => {
  // const multipart = new multiparty.Form()
  const multipart = new formidable.IncomingForm()
  multipart.on('error', function (err) {
    logger.log('verbose', `handleFormData : Watcher error: ${err}`)
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.render('errorLogin', {
      msg: '請再重新上傳一次',
      data: JSON.stringify({
        err: err,
        date: dateFormat()
      })
    })
  })
  multipart.parse(req, async (err, fields, files) => {
    if (err) {
      logger.log('verbose', `multipart.parse error: ${err}`)
      res.render('errorLogin', {
        msg: 'multipart parse error',
        data: JSON.stringify({
          err: err,
          date: dateFormat()
        })
      })
    } else {
      // console.log(fields, files)
      const { filepath } = files.chunk
      // const [ chunk ] = files.chunk
      const { hash, fileHash } = fields
      // const [ fileHash ] = fields.fileHash
      // const [ filename ] = fields.filename

      const filePath = path.resolve(UPLOAD_DIR, `${fileHash}}`)
      const chunkDir = path.resolve(UPLOAD_DIR, fileHash)

      // 文件存在直接返回
      if (fse.existsSync(filePath)) {
        res.setHeader('content-type', 'application/json; charset=utf-8')
        res.json({
          code: 20000,
          msg: '文件已經存在',
          data: JSON.stringify({
            shouldUpload: false,
            date: dateFormat()
          })
        })
        return
      }

      // 切片目錄不存在則創建目錄
      if (!fse.existsSync(chunkDir)) {
        console.log('chunkDir', chunkDir)
        await fse.mkdirs(chunkDir)
      }

      //like fs.rename
      await fse.move(filepath, path.resolve(chunkDir, hash))
      // await fse.move(chunk.path, path.resolve(chunkDir, hash))
      res.setHeader('content-type', 'application/json; charset=utf-8')
      res.json({
        code: 20000,
        msg: 'Success',
        data: JSON.stringify({
          date: dateFormat()
        })
      })
    }
  })
}

const handleMerge = async (req, res) => {
  try {
    const { fileHash, filename, size } = req.body
    logger.log('info', `File ${filename} is handling Merge`)
    const ext = path.extname(filename)
    const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
    // console.log("合併切片filePath:",filePath)
    await mergeFileChunk(filePath, fileHash, size)

    logger.log('info', `File ${filename} is Merge success`)
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.json({
      code: 20000,
      msg: '上傳成功！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } catch (err) {
    logger.log('verbose', `handleMerge : Watcher error: ${err}`)
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.json({
      code: 40100,
      msg: err,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleDownload = (req, res) => {
  const { filename } = req.params
  const absFile = path.join(CREATE_DIR, `${filename}`)
  var fileSizeInBytes = fse.statSync(absFile).size
  res.setHeader('Content-Length', fileSizeInBytes)
  res.download(path.join(CREATE_DIR, `${filename}`))
}

module.exports = {
  handleVerify,
  handleFormData,
  handleMerge,
  handleDownload
}
